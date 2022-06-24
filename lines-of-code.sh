#/bin/sh

# echo "Current: $(git ls-files -z ${1} | xargs -0 cat | wc -l)"

git log --pretty=tformat: --numstat | gawk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "Added lines: %s removed lines: %s total lines: %s\n", add, subs, loc }' -
