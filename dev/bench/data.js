window.BENCHMARK_DATA = {
  "lastUpdate": 1784581734191,
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
      }
    ]
  }
}