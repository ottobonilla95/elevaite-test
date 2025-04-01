import sys
import json
import os


def main():
    output_path = "/opt/ml/processing/output/task1_output.json"
    task1_output = {"task1_output": "output_from_task1"}

    with open(output_path, "w") as f:
        json.dump(task1_output, f)

    print(f"main() executed, saved task1_output to {output_path}")


def run_generate_topics():
    input_path = "/opt/ml/processing/output/task1_output.json"
    output_path = "/opt/ml/processing/output/task2_output.json"

    if os.path.exists(input_path):
        with open(input_path, "r") as f:
            data = json.load(f)
            input_value = data.get("task1_output", "default_value")
    else:
        input_value = "default_value"

    task2_output = {"task2_output": input_value + "_processed"}

    with open(output_path, "w") as f:
        json.dump(task2_output, f)

    print(f"run_generate_topics() executed, saved task2_output to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--entrypoint":
        entrypoint = sys.argv[2]
        if entrypoint == "main":
            main()
        elif entrypoint == "run_generate_topics":
            run_generate_topics()
        else:
            print(f"Unknown entrypoint: {entrypoint}")
    else:
        main()
