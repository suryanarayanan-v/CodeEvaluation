import os


def read_and_print_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print("File content:")
            print("=============")
            print(content)
            print("=============")
            print("End of file.")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"Error: {e}")


file_path = os.path.join('bloglist', 'controllers', 'blogs.js')

read_and_print_file(file_path)
