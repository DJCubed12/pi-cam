import re

PATTERN = r"\?file=([-_a-zA-Z0-9]+\.(mp4|h264))$"


def testRegex(pattern: re.Pattern):
    inp = "overwrite me"
    while inp:
        inp = input("TEST: ")
        m = pattern.match(inp)
        if m:
            print("MATCH:", m)
            print("GROUPS:", m.groups())
        else:
            print("NO MATCH")


if __name__ == "__main__":
    testRegex(re.compile(PATTERN))
