import os


def clone_github_repo(repo_url):
    try:
        os.system(f"git clone {repo_url}")
        print(f"Repository cloned successfully: {repo_url}")
    except Exception as e:
        print(f"Failed to clone the repository. Error: {e}")


if __name__ == "__main__":
    if not os.path.exists('fullstackopen'):
        clone_github_repo('https://github.com/suryanarayanan-v/fullstackopen.git')
