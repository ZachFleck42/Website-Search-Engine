ALPHABET_SIZE = 256

def RKsearch(pat, txt, q=13):
    results = []
    M = len(pat)
    N = len(txt)
    i = 0
    j = 0
    p = 0
    t = 0
    h = 1

    for i in range(M-1):
        h = (h*ALPHABET_SIZE) % q

    for i in range(M):
        p = (ALPHABET_SIZE*p + ord(pat[i])) % q
        t = (ALPHABET_SIZE*t + ord(txt[i])) % q

    for i in range(N-M+1):
        if p == t:
            for j in range(M):
                if txt[i+j] != pat[j]:
                    break

            j += 1
            if j == M:
                results.append(i)

        if i < N-M:
            t = (ALPHABET_SIZE*(t-ord(txt[i])*h) + ord(txt[i+M])) % q
            if t < 0:
                t = t+q

    return results