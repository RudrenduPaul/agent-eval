window.BENCHMARK_DATA = {
  "lastUpdate": 1784597541832,
  "repoUrl": "https://github.com/RudrenduPaul/agent-eval",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "RudrenduPaul@users.noreply.github.com",
            "name": "Rudrendu",
            "username": "RudrenduPaul"
          },
          "committer": {
            "email": "RudrenduPaul@users.noreply.github.com",
            "name": "Rudrendu",
            "username": "RudrenduPaul"
          },
          "distinct": true,
          "id": "b174b81457ae3fe6526a478aded774e6e79bfb9a",
          "message": "Correct false json-repair fix claim; gh-pages branch created separately\n\nRound-2 audit caught that the earlier CHANGELOG claim of bumping\njson-repair past its advisory never actually took effect: crewai pins\njson-repair~=0.25.2, which caps resolution below the 0.60.1 fix, so\nuv.lock is unchanged at 0.25.3 and the Dependabot alert is still open.\nCorrected the record instead of leaving a false claim standing.\n\n(gh-pages branch, needed by benchmark.yml's publish step, was created\ndirectly on the remote -- no local repo changes for that fix.)",
          "timestamp": "2026-07-20T14:08:35-07:00",
          "tree_id": "655585194124e7ea4b6fea8ff17e2c5107d9d58c",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/b174b81457ae3fe6526a478aded774e6e79bfb9a"
        },
        "date": 1784581733896,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2335.8755790830105,
            "unit": "iter/sec",
            "range": "stddev: 0.000022136113866534145",
            "extra": "mean: 428.10499367118166 usec\nrounds: 790"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1523.4130144226583,
            "unit": "iter/sec",
            "range": "stddev: 0.00002059397097385141",
            "extra": "mean: 656.4208067888793 usec\nrounds: 1149"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.784887205248303,
            "unit": "iter/sec",
            "range": "stddev: 0.00028650559030852845",
            "extra": "mean: 40.34716767999839 msec\nrounds: 25"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "RudrenduPaul@users.noreply.github.com",
            "name": "Rudrendu",
            "username": "RudrenduPaul"
          },
          "committer": {
            "email": "RudrenduPaul@users.noreply.github.com",
            "name": "Rudrendu",
            "username": "RudrenduPaul"
          },
          "distinct": true,
          "id": "b86f7e220931c6f10e1519b1cfe30ddca76e7942",
          "message": "Add docs/validation.md: full 29-PR list backing the \"all 29 now pass\" claim\n\npr-analysis.md only ever had detailed writeups for a 14-PR\nrepresentative slice. The dev.to article's claim that \"all 29 now\npass\" needs the full evidence to be publicly checkable, not just the\nsample. This adds the remaining 15 rows with real PR links where one\nwas on record, and an honest \"PR number not on record\" note where it\nwasn't, rather than fabricating one. One of the 6 PR numbers pulled\nfrom internal tracking (#1167) did not independently verify against\nthe real repo and is excluded rather than published unverified.",
          "timestamp": "2026-07-20T18:32:03-07:00",
          "tree_id": "5e226bfe21de7439415e3e67121c3c29bbde1303",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/b86f7e220931c6f10e1519b1cfe30ddca76e7942"
        },
        "date": 1784597541570,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1882.6998538868115,
            "unit": "iter/sec",
            "range": "stddev: 0.000018108200111165282",
            "extra": "mean: 531.1521100591323 usec\nrounds: 845"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1299.7813283084176,
            "unit": "iter/sec",
            "range": "stddev: 0.000017983899145586274",
            "extra": "mean: 769.3601825327312 usec\nrounds: 1145"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.97970613441148,
            "unit": "iter/sec",
            "range": "stddev: 0.0004971919476299369",
            "extra": "mean: 38.49158242307628 msec\nrounds: 26"
          }
        ]
      }
    ]
  }
}