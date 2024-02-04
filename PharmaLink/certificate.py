# import os
# import os.path
# import ssl
# import stat
# import subprocess
# import sys

# STAT_0o775 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
#               stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
#               stat.S_IROTH | stat.S_IXOTH)

# def main():
#     # Get the user-specific bin directory
#     user_bin_dir = os.path.expanduser("~/.local/bin")

#     print(" -- pip install --upgrade certifi")
#     subprocess.check_call([sys.executable,
#         "-E", "-s", "-m", "pip", "install", "--upgrade", "--user", "certifi"])

#     # Add user-specific bin directory to PATH
#     os.environ["PATH"] = f"{user_bin_dir}:{os.environ['PATH']}"

#     import certifi

#     # Rest of your script...

# if __name__ == '__main__':
#     main()
