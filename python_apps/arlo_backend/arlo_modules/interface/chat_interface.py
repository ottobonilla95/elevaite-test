
class GradioInterface:
    def __init__(self, chat_service, knowledge_service, web_search_service, streaming=True):
        self.chat_service = chat_service
        self.streaming = streaming
        self.knowledge_service = knowledge_service
        self. web_search_service = web_search_service
        self.chat_history = []
        self.chat_display = []

    def create_interface(self):
        with gr.Blocks() as demo:
            chatbot = gr.Chatbot(type="messages",
                                 avatar_images=(
                                     "./icons/user.png",
                                     "./icons/chatbot.png"),
                                 )

            msg = gr.Textbox(label="Ask a question", lines=5)
            web_results = gr.Textbox(label="Web Results", lines=5)
            kb_results = gr.Textbox(label="Knowledge Base Results", lines=5)
            clear = gr.ClearButton([msg, chatbot, web_results, kb_results])
            reset_button = gr.Button("Reset Chat History")

            def reset_chat():
                self.chat_history = []
                self.chat_display = []
                return [], "", "", ""

            def respond(message):
                self.chat_history.append(("user", message))
                self.chat_display.append({"role": "user", "content": message})
                self.chat_display.append({"role": "assistant", "content": "Thinking..."})

                # yield "", self.chat_display, "", ""

                kb_text = self.knowledge_service(message)
                solution = ""
                web_text = self.web_search_service(message)

                all_articles = "Knowledge Base Articles\n\n" + kb_text + "Web Search results\n\n" + web_text

                if self.streaming:
                    print("Streaming response in chat service")
                    for response in self.chat_service(message, all_articles, self.chat_history, streaming=True):
                        solution += response
                        self.chat_display[-1] = {"role": "assistant", "content": solution}

                        yield "", self.chat_display, web_text, kb_text

                    self.chat_history.append(("assistant", solution))
                else:
                    # print("Generating response in chat service")
                    # print("Message: ", message)
                    # print("KB Text: ", kb_text[:100])
                    # print("Web Text: ", web_text[:100])
                    # print("Chat History: ", self.chat_history)
                    solution = next(self.chat_service(message, all_articles, self.chat_history, streaming=False))
                    # print(solution if isinstance(solution, str) else solution.content)
                    self.chat_display[-1] = {"role": "assistant", "content": solution}
                    self.chat_history.append(("assistant", solution))
                    yield "", self.chat_display, web_text, kb_text

                # print(self.chat_history)
                # print(self.chat_display)
                return "", self.chat_display, web_text, kb_text

            msg.submit(respond, [msg], [msg, chatbot, web_results, kb_results], queue=True)
            reset_button.click(reset_chat, [], [chatbot, web_results, kb_results, msg])
            clear.click(reset_chat, [], [chatbot, web_results, kb_results, msg])

        return demo