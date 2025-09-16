def solution(arr):
    """
    arr: flat list like ["A","B",5, "A","C",10, "B","C",15, "C","A",20, "A", 2]
         (edges as triples, then start, then k)
    returns: max achievable total profit (int), with <= k trades and no revisits
    """
    if not arr or len(arr) < 5:
        return 0

    start = arr[-2]
    k = int(arr[-1])
    triples = arr[:-2]
    if len(triples) % 3 != 0:
        raise ValueError("Malformed input: edge triples are incomplete")

    # Build adjacency without defaultdict
    adj = {}
    max_pos_edge = 0
    for i in range(0, len(triples), 3):
        u = triples[i]
        v = triples[i + 1]
        w = int(triples[i + 2])
        if u in adj:
            adj[u].append((v, w))
        else:
            adj[u] = [(v, w)]
        if w > max_pos_edge:
            max_pos_edge = w

    # Sort outgoing edges by descending profit to tighten pruning early
    for u in adj:
        adj[u].sort(key=lambda x: x[1], reverse=True)

    # Upper bound only benefits if positive
    max_pos_edge = max(0, max_pos_edge)

    best = 0
    if k <= 0:
        return best

    # If start has no outgoing edges, zero trades (profit 0) is optimal
    if start not in adj:
        return 0

    visited = set([start])

    def dfs(u, depth, curr):
        nonlocal best
        if curr > best:
            best = curr
        if depth == k:
            return

        remaining = k - depth

        # Global optimistic bound prune
        if max_pos_edge == 0 or curr + remaining * max_pos_edge <= best:
            return

        out = adj.get(u)
        if not out:
            return

        for v, w in out:
            if v in visited:
                continue

            new_curr = curr + w
            rem_after = remaining - 1

            # Child-specific bound prune
            if rem_after >= 0 and new_curr + rem_after * max_pos_edge <= best:
                continue

            visited.add(v)
            dfs(v, depth + 1, new_curr)
            visited.remove(v)

    dfs(start, 0, 0)
    return best


# Example:
# arr = ["A","B",5,"A","C",10,"B","C",15,"C","A",20,"A",2]
# print(solution(arr))  # -> 20
