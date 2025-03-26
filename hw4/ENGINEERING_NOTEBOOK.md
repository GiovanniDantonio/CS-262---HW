# Engineering Notebook: Dynamic Server Addition in Distributed Chat System

## Hypothesis

I hypothesized that implementing dynamic server addition in our Raft-based chat system would enhance its scalability without compromising fault tolerance. The key challenge would be maintaining consistency during the addition of new servers while ensuring the system remains operational. I predicted that a two-phase approach (non-voting member followed by promotion) would provide the safest path to cluster expansion.

## What I Did

Oh boy, what a journey this has been! 🚀 I started by diving headfirst into the fascinating world of dynamic membership changes in distributed systems - and let me tell you, it's like trying to change the wheels on a moving car while keeping all the passengers comfortable. Not exactly a walk in the park!

First, I extended our existing Raft implementation to support non-voting members. This was particularly interesting because these servers are like the interns of the distributed world - they get all the updates but don't get to vote yet. I found myself chuckling at the parallel with real-world organizations: "Sorry, new server, you'll get voting rights after your probation period!" 

The implementation journey took several fascinating turns. I encountered my first major challenge when dealing with log replication for new servers. Picture this: a new server joins and asks, "What'd I miss?" and suddenly needs to catch up on potentially thousands of entries. My initial naive approach of sending everything at once was like trying to drink from a fire hose - it overwhelmed both the leader and the new server. The solution? A more graceful, paginated approach to log transfer that felt more like a civilized conversation than a data dump.

One particularly tricky bug had me scratching my head for hours. The new server would catch up with the log, but occasionally miss a few entries that arrived during the catch-up process. It was like trying to fill a bucket with water while someone keeps adding more - you never quite know when to stop! I solved this by implementing a clever "double-check" mechanism where the new server verifies it hasn't missed anything before requesting promotion to voting member.

The most satisfying moment came when implementing the promotion phase. It's like watching a graduation ceremony - the server has caught up with all the logs, proven its reliability, and finally gets to join the "voting club." I added extra validation to ensure the promotion only happens when the new server is truly ready, preventing any premature promotions that could compromise system stability.

Looking ahead, there are several exciting possibilities for improvement. I'm particularly interested in implementing automatic log compaction to prevent the catch-up phase from becoming too lengthy as the system runs for extended periods. Additionally, adding support for removing servers would complete the dynamic membership feature set.

One unexpected challenge was maintaining quorum requirements during the transition period. Should we count non-voting members when determining system availability? After careful consideration and some enlightening discussions with the literature, I decided to maintain strict quorum requirements based only on voting members, ensuring system safety during membership changes.

The testing phase was particularly entertaining. I simulated various failure scenarios, including the classic "Murphy's Law" test - what happens if everything that can go wrong, does go wrong? This included scenarios like the leader failing mid-promotion, network partitions during catch-up, and my personal favorite: the "chaos monkey" test where we randomly killed servers during membership changes. The system's resilience in these scenarios was both impressive and reassuring.

For future work, I'm excited about the possibility of implementing automatic cluster scaling based on load metrics. Imagine a self-managing cluster that grows and shrinks based on demand - now that would be something! I'm also considering adding a "server health check" feature that could proactively identify and replace failing nodes before they cause issues.

Throughout this project, I gained a deeper appreciation for the complexities of distributed systems. It's one thing to read about them in papers, but actually implementing these concepts brings a whole new level of understanding. As Professor Ding often emphasizes, the devil is in the details, and this project certainly proved that point!

## Next Steps

1. Implement automatic log compaction to optimize the catch-up phase
2. Add support for graceful server removal
3. Develop automated testing scenarios for membership changes
4. Consider implementing automatic cluster scaling based on load metrics
5. Add comprehensive monitoring and visualization of cluster state changes

## Challenges and Solutions

| Challenge | Solution | Outcome |
|-----------|----------|----------|
| Log catch-up overwhelming servers | Implemented paginated log transfer | Smooth, controlled catch-up process |
| Missing entries during catch-up | Added double-check verification | Guaranteed consistency |
| Quorum management | Strict voting-member-only policy | Maintained system safety |
| Leader failures during promotion | Implemented promotion retry mechanism | Robust membership changes |

## Lessons Learned

1. Always consider edge cases in distributed systems - they're not edge cases, they're Tuesday!
2. Incremental changes and thorough testing are crucial for system stability
3. Clear documentation and logging are invaluable for debugging distributed systems
4. The importance of graceful degradation and failure handling
5. The value of a well-designed testing strategy
