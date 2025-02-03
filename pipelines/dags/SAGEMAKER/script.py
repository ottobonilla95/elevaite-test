import sys


def main():
    task1_output = "output_from_task1"
    # Inject the output into the global namespace so that the json2sagemaker executor can pick it up
    globals()["task1_output"] = task1_output
    print("main() executed, produced task1_output =", task1_output)


def run_generate_topics():
    # Retrieve input from globals (populated by the previous task)
    input_value = globals().get("task1_output", "default_value")
    task2_output = input_value + "_processed"
    globals()["task2_output"] = task2_output
    print("run_generate_topics() executed, produced task2_output =", task2_output)


if __name__ == "__main__":
    # When called from the command line, expect the entrypoint function name as an argument.

    if len(sys.argv) > 1:
        entrypoint = sys.argv[1]
        if entrypoint == "main":
            main()
        elif entrypoint == "run_generate_topics":
            run_generate_topics()
        else:
            print(f"Unknown entrypoint: {entrypoint}")
    else:
        # Default action when no entrypoint is provided.
        main()
