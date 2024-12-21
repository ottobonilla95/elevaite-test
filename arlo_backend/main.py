import os
from starlette.middleware.cors import CORSMiddleware
from data_models import ChatRequestWithQueryId, SummaryInputModel, SummaryRequest
from arlo_modules.config.settings import Prompts
from arlo_bot import chat_service, web_search_service, ds_rag_service, craft_query, web_summarize_service, kb_summarize_service
from fastapi import FastAPI, Body
from summarize_agent import extract_summary
import datetime
import uuid
from data_models import *
from models import ChatDBMethods
import concurrent.futures
import dotenv
import json
from main_psql import get_opexwise_data
from Salesforce_PythonModule.src.salesforce_service import get_sf_case, save_summary_to_salesforce
# from cache_control import CacheControl

dotenv.load_dotenv()
knowledge_service = None

origins = [
    "http://127.0.0.1:3004",
    "http://127.0.0.1:3005",
    "https://127.0.0.1:3004",
    "https://127.0.0.1:3005",
    "http://127.0.0.1",
    "http://localhost:3004",
    "http://localhost:3006",
    "http://localhost",
    "https://elevaite-arlocb.iopex.ai",
    "http://elevaite-arlocb.iopex.ai",
    ]


app = FastAPI(title="Arlo AI Chatbot API")

class GradioInterface:
    def __init__(self, app, chat_service, knowledge_service, web_search_service, ds_rag_service, streaming=True):
        self.app = app
        self.chat_service = chat_service
        self.streaming = streaming
        self.knowledge_service = knowledge_service
        self.ds_rag_service = ds_rag_service
        self.web_search_service = web_search_service
        self.web_toggle = True
        self.summarize = True
        self.qa = False
        self.prompt_box = Prompts.DEFAULT_SYSTEM_PROMPT
        self.qa_prompt_box = Prompts.QA_SYSTEM_PROMPT

    def create_inference_step(self, step_name,step_start_time, step_input_label, step_output_label, step_input, step_output):
        inference_step = ChatInferenceStepInfo(
            step_name=step_name,
            step_input_label=step_input_label,
            step_output_label=step_output_label,
            start_time=step_start_time,
            step_input=step_input,
            step_output=step_output,
            end_time=datetime.datetime.now()
        )

        return inference_step


    def create_session_data(self, user_id, query_id, session_id, query, query_timestamp, inference_steps, response):
        query_id = query_id
        response_timestamp = datetime.datetime.now()
        chat_json = ChatSessionDataResponse(
            query=query,
            query_timestamp=query_timestamp,
            inference_steps=inference_steps,
            response=response,
            response_timestamp=response_timestamp
        )

        chat_timestamp = query_timestamp

        chat_session_data = ChatSessionDataModel(
            chat_timestamp=chat_timestamp,
            session_id=session_id,
            query_id=query_id,
            user_id=user_id,
            chat_json=chat_json
        )

        return chat_session_data

    def process_chat(self, message, chat_history, session_id=None, user_id=None, fetched_knowledge=""):
        query_id = uuid.uuid4()
        # r = CacheControl()
        query = message
        query_timestamp = datetime.datetime.now()
        inference_steps = []
        chat_display = []
        chat_history = []
        url_refs = []
        self.prompt_box = Prompts.VERIFICATION_SYSTEM_PROMPT

        solution_start_time = datetime.datetime.now()
        solution = "".join(response for response in self.chat_service(
            message, fetched_knowledge, chat_history, streaming=self.streaming,
            system_prompt=self.prompt_box, qa=self.qa, qa_system_prompt=self.qa_prompt_box
        ))
        print("Solution: ", solution)

        try:
            solution = json.loads(solution)
            extracted_information = "\n\n".join([str(i)+": "+solution["extracted_information"][i] for i in solution["extracted_information"]])
            welcome_message = solution["welcome_message"]
            verification_message = solution["verification_message"]
            issue_acknowledgement = solution["issue_acknowledgement"]
            try:
                opex_data = get_opexwise_data(contact_email=solution["extracted_information"]["Email"].lower())
            except:
                opex_data = []
        except:
            welcome_message = "Welcome to Arlo's chat service. Please give me 2 minutes to go over the issue?"
            extracted_information = "Could not extract any information from the chat."
            verification_message = "Could not verify the details."
            issue_acknowledgement = "Could not acknowledge the issue."
            opex_data = []

        # r.hset(session_id, "chat_context",fetched_knowledge)
        # r.expire(session_id, 3600)

        inference_steps.append(self.create_inference_step(
            step_name="Response Generation",
            step_start_time=solution_start_time,
            step_input_label="Fetched Knowledge",
            step_output_label="Response",
            step_input="\n".join([extracted_information, verification_message, issue_acknowledgement]),
            step_output=welcome_message
        ))
        chat_display.append({"role": "assistant", "content": welcome_message})
        if not self.streaming:
            chat_history.append(("assistant", welcome_message))


        return (self.create_session_data(user_id=user_id,
                                         session_id=session_id,
                                         query_id=query_id,
                                         query=query,
                                         query_timestamp=query_timestamp,
                                         inference_steps=inference_steps,
                                         response=welcome_message), url_refs[:3],
                                        extracted_information, verification_message, issue_acknowledgement,
                                        opex_data)

    def process_sf_chat(self, message, session_id=None, user_id=None):
        query_id = uuid.uuid4()
        # r = CacheControl()
        query = message
        query_timestamp = datetime.datetime.now()
        inference_steps = []
        chat_display = []
        chat_history = []
        url_refs = []
        self.prompt_box = Prompts.VERIFICATION_SYSTEM_PROMPT_SF

        solution_start_time = datetime.datetime.now()
        solution = "".join(response for response in self.chat_service(
            message, "", chat_history, streaming=self.streaming,
            system_prompt=self.prompt_box, qa=self.qa, qa_system_prompt=self.qa_prompt_box
        ))
        print("Solution: ", solution)

        try:
            solution = json.loads(solution)
            extracted_information = "\n\n".join([str(i)+": "+solution["extracted_information"][i] for i in solution["extracted_information"]])
            welcome_message = solution["welcome_message"]
            verification_message = solution["verification_message"]
            issue_acknowledgement = solution["issue_acknowledgement"]

        except:
            welcome_message = "Welcome to Arlo's chat service. Please give me 2 minutes to go over the issue?"
            extracted_information = "Could not extract any information from the chat."
            verification_message = "Could not verify the details."
            issue_acknowledgement = "Could not acknowledge the issue."

        # r.hset(session_id, "chat_context",fetched_knowledge)
        # r.expire(session_id, 3600)

        inference_steps.append(self.create_inference_step(
            step_name="Response Generation",
            step_start_time=solution_start_time,
            step_input_label="Fetched Knowledge",
            step_output_label="Response",
            step_input="\n".join([extracted_information, verification_message, issue_acknowledgement]),
            step_output=welcome_message
        ))
        chat_display.append({"role": "assistant", "content": welcome_message})
        if not self.streaming:
            chat_history.append(("assistant", welcome_message))


        return (self.create_session_data(user_id=user_id,
                                         session_id=session_id,
                                         query_id=query_id,
                                         query=query,
                                         query_timestamp=query_timestamp,
                                         inference_steps=inference_steps,
                                         response=welcome_message), url_refs[:3],
                                        extracted_information, verification_message, issue_acknowledgement)

    def respond(self, message, chat_history, session_id=None, user_id=None, fetched_knowledge=""):
        query_id = uuid.uuid4()
        # r = CacheControl()
        in_cache=False
        query = message
        query_timestamp = datetime.datetime.now()
        inference_steps = []
        chat_display = []
        begin_time = datetime.datetime.now()
        for c in chat_history:
            chat_display.append({"role": c[0], "content": c[1]})
        if chat_history:
            ChatDBMethods.save_chat_history(ChatHistoryModel(query_id=query_id,
                                               session_id=uuid.UUID(session_id),
                                               user_id=user_id,
                                               chat_timestamp=query_timestamp,
                                               chat_json=ChatHistory(chat_json=chat_display)))
        else:
            print("No chat history to save")


        crafted_query_step = self.create_inference_step(
            step_name="Crafting Query",
            step_start_time=query_timestamp,
            step_input_label="User Query",
            step_output_label="Crafted Query",
            step_input=message,
            step_output=next(craft_query(message, chat_display))
        )

        print("Crafted Query Step time: ",  datetime.datetime.now() - begin_time)
        begin_time = datetime.datetime.now()

        inference_steps.append(crafted_query_step)
        try:
            crafted_query_and_intent = eval(crafted_query_step.step_output.strip("`").replace("json",""))
        except:
            crafted_query_and_intent = {"intent": "troubleshooting", "crafted_query": message}
        print("Original Query: ", message)
        print("Crafted Query: ", crafted_query_and_intent)

        intent = crafted_query_and_intent["intent"].strip().lower()
        print("Intent: ", intent)
        if intent in ["pasted chat"]:
            print("Thanks for pasting the chat")
        crafted_query = crafted_query_and_intent["crafted_query"].strip().lower()
        # if r.get(crafted_query):
        #     in_cache = True

        print("Crafted Query: ", crafted_query)

        if intent in ["troubleshooting", "installation", "probing", "follow-up"]:
            self.prompt_box = Prompts.DEFAULT_SYSTEM_PROMPT_SHORT
        else:
            self.prompt_box = Prompts.DEFAULT_SYSTEM_PROMPT

        if intent in ["greeting","probing"]  or crafted_query=="":
            fetched_knowledge = ""
            response_start_time = datetime.datetime.now()
            solution = "".join(response for response in self.chat_service(
                message, fetched_knowledge, chat_history, streaming=self.streaming,
                system_prompt=Prompts.GREETING_SYSTEM_PROMPT if intent=="greeting" else "Ask the user about their product name or issue they are facing, whichever is relevant to the conversation.",
                qa=False, qa_system_prompt=self.qa_prompt_box
            ))
            chat_display.append({"role": "assistant", "content": solution})
            chat_history.append(("assistant", solution))
            response_step = self.create_inference_step(
                step_name="Response Generation",
                step_start_time=response_start_time,
                step_input_label="Crafted Query",
                step_output_label="Response",
                step_input=crafted_query,
                step_output=solution
            )
            inference_steps.append(response_step)

            return self.create_session_data(session_id=session_id,
                                            user_id=user_id,
                                            query_id=query_id,
                                            query=query,
                                            query_timestamp=query_timestamp,
                                            inference_steps=inference_steps,
                                            response=solution), [], ""
        elif "follow-up" in intent.lower():
            kb_refs = []
            url_refs = []
            # fetched_knowledge = r.hget(session_id, "fetched_knowledge")
            print("Fetched Knowledge from cache follow-up: ", fetched_knowledge[:100])
            # self.prompt_box = Prompts.DEFAULT_SYSTEM_PROMPT_SHORT
            # print("Fetching Knowledge\n",fetched_knowledge,"\n"+"-"*50)
            # print("Chat History\n",chat_history,"\n"+"-"*50)

        # elif in_cache:
        #     kb_refs = []
        #     url_refs = []
        #     fetched_knowledge = r.get(crafted_query.lower())
        #     print("Fetched Knowledge from cache: ", fetched_knowledge[:100])

        else:
            def get_kb_text():
                kb_start_time = datetime.datetime.now()
                kb_text_, kb_refs_ = self.ds_rag_service(crafted_query)
                junk_text = """Document context: the following excerpt is from a document titled 'Arlo Theft Replacement Program and End of Life Policy'. This document is about: the Arlo Theft Replacement Program and End of Life Policy, detailing the eligibility, procedures, and conditions for replacing stolen Arlo devices and the discontinuation of support for older Arlo products."""
                kb_text_ = kb_text_.replace(junk_text, "")
                kb_retrieval_step = self.create_inference_step(
                    step_name="Knowledge Base Retrieval",
                    step_start_time=kb_start_time,
                    step_input_label="Crafted Query",
                    step_output_label="KB Text",
                    step_input=crafted_query,
                    step_output=kb_text_,
                )
                if os.environ.get("SUMMARIZE") == "True":
                    kb_summary = kb_summarize_service(crafted_query, kb_text_, chat_history)
                    kb_summary_step = self.create_inference_step(
                        step_name="KB Summarization",
                        step_start_time=datetime.datetime.now(),
                        step_input_label="KB Text",
                        step_output_label="KB Summary",
                        step_input=kb_text_,
                        step_output=kb_summary,
                    )
                    return kb_summary, kb_refs_, [kb_retrieval_step, kb_summary_step]
                else:
                    return kb_text_, kb_refs_, [kb_retrieval_step]


            def get_web_text():
                try:
                    web_ret_start_time = datetime.datetime.now()
                    web_text_, urls_fetched = self.web_search_service(crafted_query)
                    url_refs_ = list(urls_fetched)
                    inference_step = self.create_inference_step(
                        step_name="Web Search",
                        step_start_time=web_ret_start_time,
                        step_input_label="Crafted Query",
                        step_output_label="Web Text",
                        step_input=crafted_query,
                        step_output=web_text_,
                    )
                    if os.environ.get("SUMMARIZE") == "True":
                        web_summary_start_time = datetime.datetime.now()
                        web_summary = web_summarize_service(crafted_query,web_text_, chat_history)
                        web_summary_step = self.create_inference_step(
                            step_name="Web Summarization",
                            step_start_time=web_summary_start_time,
                            step_input_label="Web Text",
                            step_output_label="Web Summary",
                            step_input=web_text_,
                            step_output=web_summary,
                        )
                        return web_summary, url_refs, [inference_step, web_summary_step]
                    else:
                        return web_text_, url_refs_, [inference_step]
                except:
                    return "Web Search could not be performed", [], []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                kb_future = executor.submit(get_kb_text)
                web_future = executor.submit(get_web_text)
                web_text, url_refs, web_inference_step = web_future.result()
                kb_text, kb_refs, kb_inference_step = kb_future.result()

            inference_steps+=kb_inference_step
            if web_inference_step:
                inference_steps+=web_inference_step

            fetched_knowledge = (
                "Here is the only information you can use to solve the issue: \n\n"
                f"Knowledge Base Articles\n\n{kb_text}\n\nKnowledge Base Search results\n\n{web_text}\n\n"
                "End of relevant information from the knowledge base."
            )

            # r.set(crafted_query.lower(), fetched_knowledge)
            # r.expire(crafted_query, 3600)


        # r.hset(session_id, "fetched_knowledge",fetched_knowledge)
        # r.expire(session_id, 3600)
        # print("Fetched Knowledge: ", fetched_knowledge)
        # print("Chat history: ", chat_history)
        # print("Message :", message)
        # print("Chat history: ", chat_history)

        print("Fetching Knowledge Step time: ", datetime.datetime.now() - begin_time)
        begin_time = datetime.datetime.now()

        solution_start_time = datetime.datetime.now()
        solution = "".join(response for response in self.chat_service(
            message, fetched_knowledge, chat_history, streaming=self.streaming,
            system_prompt=self.prompt_box, qa=self.qa, qa_system_prompt=self.qa_prompt_box
        ))

        inference_steps.append(self.create_inference_step(
            step_name="Response Generation",
            step_start_time=solution_start_time,
            step_input_label="Fetched Knowledge",
            step_output_label="Response",
            step_input=fetched_knowledge,
            step_output=solution
        ))
        chat_display.append({"role": "assistant", "content": solution})
        if not self.streaming:
            chat_history.append(("assistant", solution))

        if kb_refs:
            url_refs += kb_refs

        print("Solution Step time: ", datetime.datetime.now() - begin_time)

        return (self.create_session_data(user_id=user_id,
                                        session_id=session_id,
                                        query_id=query_id,
                                        query=query,
                                        query_timestamp=query_timestamp,
                                        inference_steps=inference_steps,
                                        response=solution), url_refs[:3], fetched_knowledge)


# Create the GradioInterface instance
gi = GradioInterface(
    app=app,
    chat_service=chat_service,
    knowledge_service=knowledge_service,
    web_search_service=web_search_service,
    ds_rag_service=ds_rag_service,
)


@app.post("/processSFChat", response_model=SFResponse)
def processSFChat(request: SFChatRequest=Body(...)):
    session_id = request.session_id
    user_id = request.user_id
    case_id = request.case_id

    try:
        case_information = dict(get_sf_case(case_id))
        del case_information["attributes"]
        case_information = {str(key): str(case_information[key]) for key in case_information}
    except:
        case_information = {
            "CaseNumber": case_id,
            "Subject": "Case not found",
            "Status": "Case not found",
            "AccountId": "Case not found"
        }

    message = "\n".join([f"{key}: {case_information[key]}" for key in case_information])
    print(message)

    response_chat, urls_fetched, extracted_information, verification_message, issue_acknowledgement = gi.process_sf_chat(message, session_id, user_id)

    response = SFResponse(
        response=response_chat.chat_json.response,
        fetched_knowledge="",
        urls_fetched=urls_fetched,
        query_id=str(response_chat.query_id),
        extracted_information=extracted_information,
        verification_message=verification_message,
        issue_acknowledgement=issue_acknowledgement,
        sf_data=[case_information]
    )


    return response

@app.post("/pasteChat", response_model=ChatResponse)
def pastechat(request: ChatRequest=Body(...)):
    # TODO - fix chat history order
    message = request.message
    previous_chats = request.chat_history
    fetched_knowledge = request.fetched_knowledge
    session_id = request.session_id
    user_id = request.user_id

    chat_history = []
    for i in range(len(previous_chats)):
        chat_history.append((previous_chats[i]['actor'], previous_chats[i]['content']))

    response_chat, urls_fetched, extracted_information, verification_message, issue_acknowledgement, \
        opex_data = gi.process_chat(message,chat_history, session_id, user_id, fetched_knowledge)

    for inference_step in response_chat.chat_json.inference_steps:
        print("\nInference Step: ", inference_step.step_name)
    ChatDBMethods.save_response_chat(response_chat)
    return {
        "response": response_chat.chat_json.response,
        "query_id": str(response_chat.query_id),
        "urls_fetched": [],
        "extracted_information": extracted_information,
        "verification_message": verification_message,
        "issue_acknowledgement": issue_acknowledgement,
        "opex_data": opex_data,
    }

@app.post("/chat", response_model=ChatResponse)
@app.post("/welcome", response_model=ChatResponse)
def chat(request: ChatRequest=Body(...)):
    # TODO - fix chat history order
    # print("Request: ", request)
    message = request.message
    previous_chats = request.chat_history
    # print("Previous chats: ", previous_chats)
    # print("session_id: ", request.session_id)
    fetched_knowledge = request.fetched_knowledge
    # print("Fetched Knowledge: ", fetched_knowledge)
    session_id = request.session_id
    user_id = request.user_id

    # enable_web_search = request.enable_web_search
    enable_web_search = True
    chat_history = []
    for i in range(len(previous_chats)):
        chat_history.append((previous_chats[i]['actor'], previous_chats[i]['content']))

    # print("Chat history in Chat Request: ",chat_history)

    response_chat, urls_fetched, fetched_knowledge = gi.respond(message,chat_history, session_id, user_id, fetched_knowledge)
    # print("\nResponse: ", response_chat)
    for inference_step in response_chat.chat_json.inference_steps:
        print("\nInference Step: ", inference_step.step_name)
    ChatDBMethods.save_response_chat(response_chat)
    return {
        "response": response_chat.chat_json.response,
        "query_id": str(response_chat.query_id),
        "urls_fetched": urls_fetched,
        "fetched_knowledge": fetched_knowledge
    }


@app.post("/voting")
def voting(received_vote: ChatVoting=Body(...)):
    # query_id = uuid.UUID(received_vote.query_id)
    res = ChatDBMethods.save_vote(received_vote)
    return {"message": f"{res}"}

@app.post("/feedback")
def feedback(received_feedback: ChatFeedback=Body(...)):
    # query_id = uuid.UUID(received_feedback.query_id)
    ChatDBMethods.save_feedback(received_feedback)
    if received_feedback.vote==-1:
        ChatDBMethods.save_vote(ChatVoting(query_id=received_feedback.query_id, user_id=received_feedback.user_id, vote=-1))
    # time_of_feedback = datetime.datetime.now()
    # feedback_id = str(uuid.uuid4())
    # print(f"Received feedback for query {received_feedback.query_id} with feedback {received_feedback.feedback}")
    return {"message": f"Feedback Recorded for query {received_feedback.query_id}"}

@app.post("/regenerate")
def regenerate_response(request: ChatRequestWithQueryId=Body(...)):
    # TODO - fix chat history order
    # TODO - fix regenerate prompt
    # TODO - Implement a counter for regenerate button pressed
    # TODO - Implement a counter for copy button pressed
    # TODO - add another table to capture the previous response, query id, session id, user id, new response
    # print("Recieved request ",request)
    message = request.message
    previous_chats = request.chat_history
    session_id = request.session_id
    user_id = request.user_id
    fetched_knowledge = request.fetched_knowledge
    query_id = request.query_id
    chat_history = []
    for i in range(len(previous_chats)):
        chat_history.append((previous_chats[i]['actor'], previous_chats[i]['content']))
    # print("Chat history in Regenerate response: ",chat_history)

    response = " ".join([response for response in chat_service(f"Here is the last response generated {message}", fetched_knowledge, chat_history, streaming=True,
                 system_prompt="Read the chat history and the most recent response to regenerate a better response that aligns with Arlo's aim for exceptional customer service.", qa=False, qa_system_prompt=None)])

    # print(chat_history)
    # response_chat, urls_fetched, fetched_knowledge = gi.respond(message, chat_history, session_id, user_id)
    # save_response_chat(response_chat)
    return {
        # "response": response_chat.chat_json.response,
        "response": response,
        # "query_id": str(response_chat.query_id),
        # "urls_fetched": urls_fetched,
        # "fetched_knowledge": fetched_knowledge
    }

@app.post("/summary")
def summarize(request: SummaryRequest=Body(...)):
    session_id = request.session_id
    user_id = request.user_id
    text = request.text
    entities = {}

    print(request)

    more_context = """ """
    start_time = datetime.datetime.now()
    summary_input = SummaryInputModel(system_prompt=Prompts.SUMMARY_SYSTEM_PROMPT,
                                      text=text,
                                      entities=entities,
                                      more_context=more_context,
                                      )

    try:
        summary = extract_summary(summary_input)
        print("Summary done")
        if request.case_id:
            try:
                status = save_summary_to_salesforce(request.case_id, summary[:200])
                print("Summary saved to Salesforce")
            except Exception as e:
                status = f"Error: {e}"
            print(status)

    except:
        summary = "I am sorry, I could not generate a summary for the text provided."
    end_time = datetime.datetime.now()
    summary_id = uuid.uuid4()

    summary_data = SummaryDataModel(
        summary_id=summary_id,
        session_id=uuid.UUID(session_id),
        user_id=user_id,
        summary_timestamp_start=start_time,
        summary_timestamp_end=end_time,
        input_text=text,
        summary=summary
    )

    ChatDBMethods.save_summary_session_data(summary_data)

    # Replace new lines with <br> for HTML rendering
    summary = summary.replace("\n", "<br>")

    return {"summary": str(summary),
            "summaryID": str(summary_id),}

@app.post("/vote-summary")
def vote_summary(request: SummaryVoting=Body(...)):
    print("Received vote summary request: ", request)
    session_id = request.session_id
    user_id = request.user_id
    vote = request.vote
    summary_id = request.summary_id
    print("Received vote summary request: ", request)

    vote_summary_ = SummaryVoting(
        summary_id=summary_id,
        session_id=session_id,
        user_id=user_id,
        vote=vote
    )
    print("Vote summary: ", vote_summary_)

    res = ChatDBMethods.save_vote_summary(vote_summary_)

    return {"message": f"{res}"}

@app.get("/changeCaseID")
def change_case_id(session_id: str, case_id: str):
    try:
        print("Received request to change case ID: ", {"session_id": session_id, "case_id": case_id})
        res = ChatDBMethods.save_transcript_id(CaseID(session_id=uuid.UUID(session_id), case_id=str(case_id)))
        print("SUCCESS: ", res)
        return {"message": "Case ID updated"}
    except Exception as e:
        print("ERROR: ", e)
        return {"message": f"Error: {e}"}


@app.get("/hc")
async def root():
    return {"message": "Hello World"}

@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )

    uvicorn.run(app, port=8000, host=os.environ.get("HOST"))
