import json
import os

def create_sample(file_path, start_line, start_char, end_line, end_char, base_dir="."):
    full_path = os.path.join(base_dir, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found at {full_path}")
        return None
    except Exception as e:
        print(f"Error reading file {full_path}: {e}")
        return None

    start_line_idx = start_line - 1
    end_line_idx = end_line - 1

    start_char = start_char - 1
    end_char = end_char - 1

    # Prefix
    prefix_lines = lines[:start_line_idx]
    if start_line_idx < len(lines):
         prefix_lines.append(lines[start_line_idx][:start_char])
    prefix = "".join(prefix_lines)

    # Suffix
    suffix_lines = []
    if end_line_idx < len(lines):
         suffix_lines.append(lines[end_line_idx][end_char:])
    if end_line_idx + 1 < len(lines):
        suffix_lines.extend(lines[end_line_idx + 1:])
    suffix = "".join(suffix_lines)

    # Middle
    middle_lines = []
    if start_line_idx == end_line_idx:
        if start_line_idx < len(lines):
            middle_lines.append(lines[start_line_idx][start_char:end_char])
    else:
        if start_line_idx < len(lines):
            middle_lines.append(lines[start_line_idx][start_char:])
        middle_lines.extend(lines[start_line_idx + 1 : end_line_idx])
        if end_line_idx < len(lines):
             middle_lines.append(lines[end_line_idx][:end_char])
    middle = "".join(middle_lines)

    # Basic validation
    if not prefix and not suffix and not middle:
        print(f"Warning: Empty result for {file_path} ({start_line}-{end_line}). Check coordinates.")
        return None
    if not middle:
         # Safe if middle part is intended to be empty
         print(f"Warning: Empty middle for {file_path} ({start_line}-{end_line}). Is start >= end?")

    return {
        "file": file_path,
        "prefix": prefix,
        "suffix": suffix,
        "middle": middle,
        "meta": {"lines": f"{start_line}:{start_char + 1}-{end_line}:{end_char + 1}"}
    }

# Manually adding segments for quality
split_definitions = [
    # blogs.js
    ("bloglist/controllers/blogs.js", 7, 6, 7, 48),    # .populate(...) content
    ("bloglist/controllers/blogs.js", 12, 70, 12, 75),  # .end() vs .json({})
    ("bloglist/controllers/blogs.js", 13, 47, 13, 68),  # likes = 0 assignment logic
    ("bloglist/controllers/blogs.js", 19, 26, 25, 5),   # new Blog({...}) object content
    ("bloglist/controllers/blogs.js", 31, 1, 33, 1),  # Expect to return a response of code 201 with new blog
    ("bloglist/controllers/blogs.js", 41, 5, 43, 3),  # delete blog and return status 201
    ("bloglist/controllers/blogs.js", 45, 22, 45, 70),   # filter logic in deletion
    ("bloglist/controllers/blogs.js", 47, 25, 48, 1),   # send error json message
    ("bloglist/controllers/blogs.js", 59, 77, 60, 1),  # { new: true } option
    # users.js
    ("bloglist/controllers/users.js", 7, 1, 10, 1),     # Password length check body
    ("bloglist/controllers/users.js", 11, 30, 12, 1),  # bcrypt.hash arguments
    ("bloglist/controllers/users.js", 13, 16, 18, 1),   # new User({...}) object content
    ("bloglist/controllers/users.js", 26, 3, 26, 53),  # populate arguments
    # user_api.test.js
    ("bloglist/tests/user_api.test.js", 16, 1, 21, 1), # beforeEach setup
    ("bloglist/tests/user_api.test.js", 27, 22, 32, 1), # newUser object for short username test
    ("bloglist/tests/user_api.test.js", 33, 50, 36, 1), # .send(newUser).expect(400) chain
    ("bloglist/tests/user_api.test.js", 37, 1, 39, 63), # Assertion logic (check error message and lengths)

    # user.js - userSchemaTestJSON
    ("bloglist/models/user.js", 20, 25, 28, 1),

    # middleware.js
    ("bloglist/utils/middleware.js", 28, 1, 38, 4), # trivial error messages

    # C++ Examples:
    # noparallel.cpp
    ("parallel-programming/noparallel.cpp", 89, 5, 97, 1), # Calculate cost for older nodes
    ("parallel-programming/noparallel.cpp", 98, 5, 103, 1), # cost for current node
    ("parallel-programming/noparallel.cpp", 120, 1, 129, 1), # recursive dfs calls
    ("parallel-programming/noparallel.cpp", 31, 1, 40, 1), # trivial print function

    # taskparallel.cpp
    ("parallel-programming/taskparallel.cpp", 180, 5, 179, 1), # omp task calls
    ("parallel-programming/taskparallel.cpp", 156, 9, 189, 1), # sequential calls
    ("parallel-programming/taskparallel.cpp", 206, 1, 214, 1), # omp parallel and single call

    # dataparallelism.cpp
    ("parallel-programming/dataparallelsim.cpp", 129, 1, 141, 1), # no omp tasks
    ("parallel-programming/dataparallelsim.cpp", 212, 1, 221, 1), # omp parallel for
    ("parallel-programming/dataparallelsim.cpp", 164, 1, 188, 1), # bfs state generation
    ("parallel-programming/dataparallelsim.cpp", 190, 1, 190, 55), # break condition
]

dataset = []
project_base_dir = "projects"

for definition in split_definitions:
    sample = create_sample(*definition, base_dir=project_base_dir)
    if sample:
        dataset.append(sample)

output_filename = "completion_dataset.jsonl"
with open(output_filename, 'w', encoding='utf-8') as f:
    for entry in dataset:
        f.write(json.dumps(entry) + '\n')

print(f"Dataset created with {len(dataset)} samples in {output_filename}")