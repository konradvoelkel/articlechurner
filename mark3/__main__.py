from mark3 import markdown

if __name__ == "__main__":
    import sys
    print(markdown.markdown(sys.stdin.read()))

