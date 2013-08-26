#!/bin/sh
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments. The hook should
# exit with non-zero status after issuing an appropriate message if
# it 5 wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit".
# set -e
# set -E
git status -s | while read st f; do
    if [ "$st" == '??' ]; then
        echo "Untracked files are present, CAN'T commit" 1>&2
        exit 3
    fi
done
result="$?"
if [ ! "x$result" == 'x0' ]; then
    exit 3
fi

if git rev-parse --verify HEAD >/dev/null 2>&1
then
    against=HEAD
else
    # Initial commit: diff against an empty tree object
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# If you want to allow non-ascii filenames set this variable to true.
allownonascii=$(git config hooks.allownonascii)

# Redirect output to stderr.
exec 1>&2

# Cross platform projects tend to avoid non-ascii filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if [ "$allownonascii" != "true" ] &&
    # Note that the use of brackets around a tr range is ok here, (it's
    # even required, for portability to Solaris 10's /usr/bin/tr), since
    # the square bracket bytes happen to fall in the designated range.
    test $(git diff --cached --name-only --diff-filter=A -z $against |
      LC_ALL=C tr -d '[ -~]\0' | wc -c) != 0
then
    echo "Error: Attempt to add a non-ascii file name."
    echo
    echo "This can cause problems if you want to work"
    echo "with people on other platforms."
    echo
    echo "To be portable it is advisable to rename the file ..."
    echo
    echo "If you know what you are doing you can disable this"
    echo "check using:"
    echo
    echo "  git config hooks.allownonascii true"
    echo
    exit 1
fi

FILES_PATTERN='\.(cpp|cxx|c|hxx|hpp|h|py|sh|csh|txt|vimdir)$'
FORBIDDEN='(\t| $)'
export LANG=C
files=`git diff --cached --name-only | grep -E "$FILES_PATTERN"`
for f in $files; do
    echo "Verifying file: $f"
    egrep -Hn "$FORBIDDEN" "$f"  && \
        echo "\nTabs, or trailing spaces at the end of line;\nNOT COMMITING\n" \
        && exit 5
    egrep -Hn ".{81}" "$f" && \
        echo "\nToo long lines in $f;\n NOT COMMITING\n" \
        && exit 9
    # the following is probably pointless
    (! (unexpand -t2 "$f" | expand -t2 | diff "$f" - ) ) \
        && echo "\nIndents are inconsisternt\n NOT COMMITING\n" \
        && exit 11
done

# If there are whitespace errors, print the offending file names and fail.
exec git diff-index --check --cached $against --
