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
        "meta": {"lines": f"{start_line}:{start_char}-{end_line}:{end_char}"}
    }

# Manually adding segments for quality
split_definitions = [
    # blogs.js
    ("controllers/blogs.js", 6, 26, 7, 38),    # .populate(...) content
    ("controllers/blogs.js", 12, 46, 12, 48),  # .end() vs .json({})
    ("controllers/blogs.js", 13, 40, 13, 42),  # likes = 0 assignment logic
    ("controllers/blogs.js", 18, 20, 24, 4),   # new Blog({...}) object content
    ("controllers/blogs.js", 26, 31, 26, 31),  # Empty completion after blog.save() -> Expect user.blogs update
    ("controllers/blogs.js", 35, 42, 35, 50),  # blogToBeDeleted.user.toString() === user.id condition
    ("controllers/blogs.js", 37, 5, 37, 40),   # await Blog.findByIdAndDelete(...)
    ("controllers/blogs.js", 40, 16, 41, 23),  # user.blogs filtering logic
    ("controllers/blogs.js", 47, 14, 52, 4),   # Blog update object content
    ("controllers/blogs.js", 54, 64, 54, 74),  # { new: true } option
    # users.js
    ("controllers/users.js", 6, 24, 8, 6),     # Password length check body
    ("controllers/users.js", 10, 28, 10, 37),  # bcrypt.hash arguments
    ("controllers/users.js", 12, 18, 17, 4),   # new User({...}) object content
    ("controllers/users.js", 23, 29, 24, 52),  # populate arguments
    # user_api.test.js
    ("tests/user_api.test.js", 11, 21, 17, 6), # beforeEach setup content (hashing)
    ("tests/user_api.test.js", 27, 18, 31, 6), # newUser object for short username test
    ("tests/user_api.test.js", 33, 28, 36, 24), # .send(newUser).expect(400) chain
    ("tests/user_api.test.js", 38, 6, 39, 57), # Assertion logic (check error message and lengths)
    ("tests/user_api.test.js", 62, 28, 65, 24), # .send(newUser).expect(400) chain for duplicate user
    # middleware.js
    ("utils/middleware.js", 7, 24, 9, 4),     # tokenExtractor: getting/cleaning auth header
    ("utils/middleware.js", 13, 32, 13, 51),  # jwt.decode(request.token)
    ("utils/middleware.js", 15, 16, 15, 46),  # await User.findById(decodedToken.id)
    ("utils/middleware.js", 24, 28, 24, 70),  # errorHandler: Check for ValidationError
    ("utils/middleware.js", 26, 59, 26, 105), # errorHandler: Check for E11000
    ("utils/middleware.js", 28, 31, 28, 70),  # errorHandler: Check for TokenExpiredError
    # list_helper.js
    ("utils/list_helper.js", 8, 15, 10, 2),   # totalLikes: reducer function body
    ("utils/list_helper.js", 12, 43, 12, 57),  # totalLikes: .reduce(reducer, 0)
    ("utils/list_helper.js", 15, 26, 17, 62),  # favoriteBlog: find condition (Math.max)
    ("utils/list_helper.js", 25, 34, 27, 28),  # mostBlogs: lodash maxBy callback
    ("utils/list_helper.js", 37, 11, 40, 8),   # mostLikes: inner map/reduce logic
    ("utils/list_helper.js", 42, 30, 42, 35),  # mostLikes: lo.maxBy property 'likes'
    # models/user.js
    ("models/user.js", 5, 14, 10, 4),          # username schema definition object
    ("models/user.js", 14, 11, 19, 6),         # blogs array schema definition
    ("models/user.js", 23, 29, 27, 4),         # toJSON transform function body
]

dataset = []
project_base_dir = "bloglist"

for definition in split_definitions:
    sample = create_sample(*definition, base_dir=project_base_dir)
    if sample:
        dataset.append(sample)

output_filename = "completion_dataset.jsonl"
with open(output_filename, 'w', encoding='utf-8') as f:
    for entry in dataset:
        f.write(json.dumps(entry) + '\n')

print(f"Dataset created with {len(dataset)} samples in {output_filename}")