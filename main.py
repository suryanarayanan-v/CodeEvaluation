import os


def clone_github_repo(repo_url):
    try:
        os.system(f"git clone {repo_url}")
        print(f"Repository cloned successfully: {repo_url}")
    except Exception as e:
        print(f"Failed to clone the repository. Error: {e}")

if __name__ == "__main__":
    if not os.path.exists('projects'):
        clone_github_repo('https://github.com/suryanarayanan-v/fullstackopen.git')
        # only interested in part4 bloglist so moving that to root
        os.system("mkdir projects")
        os.system("mkdir projects/bloglist")
        os.system("mkdir projects/parallel-programming")
        os.system("cp -r fullstackopen/part4/BlogList/bloglist-backend/* ./projects/bloglist")
        os.system("rm -r fullstackopen")
        clone_github_repo("https://github.com/suryanarayanan-v/parallel-programming.git")
        os.system("cp -r parallel-programming/* ./projects/parallel-programming")
        os.system("rm -r parallel-programming")