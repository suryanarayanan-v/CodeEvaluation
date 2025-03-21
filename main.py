import os


def clone_github_repo(repo_url):
    try:
        os.system(f"git clone {repo_url}")
        print(f"Repository cloned successfully: {repo_url}")


        # only interested in part4 bloglist so moving that to root
        os.system("cp -r fullstackopen/part4/bloglist/bloglist-backend/* .")
        os.system("rm -r fullstackopen")
    except Exception as e:
        print(f"Failed to clone the repository. Error: {e}")

if __name__ == "__main__":
    if not os.path.exists('bloglist'):
        clone_github_repo('https://github.com/suryanarayanan-v/fullstackopen.git')