def solution(sources, targets, profits, start, k):
    """
    sources, targets, profits: parallel lists defining directed edges and their profit
    start: starting asset (string)
    k: maximum number of trades (int)
    Returns: int = maximum total profit with <= k trades and no revisits
    """
    n = len(sources)
    if not (len(targets) == n and len(profits) == n):
        raise ValueError("sources, targets, profits must have the same length")

    # Build adjacency list; also compute global best positive edge for pruning
    adj = {}
    max_pos_edge = 0
    for i in range(n):
        u = sources[i]
        v = targets[i]
        w = int(profits[i])
        if u in adj:
            adj[u].append((v, w))
        else:
            adj[u] = [(v, w)]
        if w > max_pos_edge:
            max_pos_edge = w

    # Explore higher-profit edges first to find good answers early (helps pruning)
    for u in adj:
        adj[u].sort(key=lambda x: x[1], reverse=True)

    max_pos_edge = max(0, max_pos_edge)  # only positive edges help the optimistic bound

    best = 0
    if k <= 0:
        return best

    # If start has no outgoing edges, best is 0 (we can choose to do 0 trades)
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

        # Global optimistic bound: even if we take the best positive edge every remaining step
        # can we beat current best? If not, prune.
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

            # Child-specific optimistic bound
            if rem_after >= 0 and new_curr + rem_after * max_pos_edge <= best:
                continue

            visited.add(v)
            dfs(v, depth + 1, new_curr)
            visited.remove(v)

    dfs(start, 0, 0)
    return best


# Example:
sources = ["A", "A", "B", "C"]
targets = ["B", "C", "C", "A"]
profits = [5, 10, 15, 20]
print(solution(sources, targets, profits, "A", 2))

