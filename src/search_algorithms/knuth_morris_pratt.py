def KMPsearch(pattern, text):
    results = []
    if not pattern:
        return

    if not text or len(pattern) > len(text):
        return

    chars = list(pattern)
    temp = [0] * (len(pattern) + 1)
    for i in range(1, len(pattern)):
        j = temp[i + 1]

        while j > 0 and chars[j] is not chars[i]:
            j = temp[j]

        if j > 0 or chars[j] == chars[i]:
            temp[i + 1] = j + 1

    j = 0
    for i in range(len(text)):
        if j < len(pattern) and text[i] == pattern[j]:
            j = j + 1
            if j == len(pattern):
                results.append(i - j)
        elif j > 0:
            j = temp[j]
            i = i - 1

    return results