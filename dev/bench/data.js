window.BENCHMARK_DATA = {
  "lastUpdate": 1784687083927,
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
          "id": "67cfb488f04f39e666a26c16d781e85118a47aa9",
          "message": "Re-record demo GIFs to stop leaking a private repo path\n\ndocs/assets/demo-2-p0-crash.gif and demo-3-cli.gif both showed a\nterminal cd'ing into a private strategy repo's scratchpad path\n(oss-ideas-execution-strategy/<session-uuid>/...) before running the\nactual demo commands. Re-recorded both from a clean path inside this\nrepo (agent-eval/crash-repro, not committed) with the identical real\ncommands and real output -- same crash, same statistics, same numbers,\njust no private path visible.\n\nAlso removed docs/demo.gif and docs/usage.gif: both were unreferenced\nby any current doc, both were broken/failed takes (command not found,\nModuleNotFoundError), and demo.gif leaked the same private path in its\ntraceback. Dead weight, no reason to keep them live in a public repo.",
          "timestamp": "2026-07-20T19:24:08-07:00",
          "tree_id": "6f079555b64b33055b31ff05dad3dbdcc07f30b4",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/67cfb488f04f39e666a26c16d781e85118a47aa9"
        },
        "date": 1784600684848,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2334.148629661361,
            "unit": "iter/sec",
            "range": "stddev: 0.00001971708728094928",
            "extra": "mean: 428.4217325719658 usec\nrounds: 789"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1508.594781217345,
            "unit": "iter/sec",
            "range": "stddev: 0.000021461065991393018",
            "extra": "mean: 662.868526691482 usec\nrounds: 1124"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.439704027282623,
            "unit": "iter/sec",
            "range": "stddev: 0.00031851929465143375",
            "extra": "mean: 39.30863342307589 msec\nrounds: 26"
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
          "id": "ad3c3c9b99f2bcfe495c1d0ce96aee82537ce293",
          "message": "Re-record demo GIFs to stop leaking a private repo path\n\ndocs/assets/demo-2-p0-crash.gif and demo-3-cli.gif both showed a\nterminal cd'ing into a private strategy repo's scratchpad path\n(oss-ideas-execution-strategy/<session-uuid>/...) before running the\nactual demo commands. Re-recorded both from a clean path inside this\nrepo (agent-eval/crash-repro, not committed) with the identical real\ncommands and real output -- same crash, same statistics, same numbers,\njust no private path visible.\n\nAlso removed docs/demo.gif and docs/usage.gif: both were unreferenced\nby any current doc, both were broken/failed takes (command not found,\nModuleNotFoundError), and demo.gif leaked the same private path in its\ntraceback. Dead weight, no reason to keep them live in a public repo.",
          "timestamp": "2026-07-20T19:24:08-07:00",
          "tree_id": "6f079555b64b33055b31ff05dad3dbdcc07f30b4",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/ad3c3c9b99f2bcfe495c1d0ce96aee82537ce293"
        },
        "date": 1784601438972,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1902.9592823114112,
            "unit": "iter/sec",
            "range": "stddev: 0.000024130565263413182",
            "extra": "mean: 525.4973184635667 usec\nrounds: 807"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1306.625164406989,
            "unit": "iter/sec",
            "range": "stddev: 0.000029337841851496917",
            "extra": "mean: 765.330430823173 usec\nrounds: 1142"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 26.241217483637868,
            "unit": "iter/sec",
            "range": "stddev: 0.00017461963902954883",
            "extra": "mean: 38.107987962964295 msec\nrounds: 27"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "38769913+RudrenduPaul@users.noreply.github.com",
            "name": "Rudrendu Paul",
            "username": "RudrenduPaul"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "395defd470abb832102b5c6ac7f28c0cd48da028",
          "message": "Document all compare flags and CLI exit codes in README (#13)\n\nThe \"In 30 seconds (CLI)\" section only documented 3 of the 8 real\nagent-regress compare flags. Add --p-threshold, --min-effect,\n--n-resamples, and the top-level --version flag with their real\ndefaults from src/agent_regress/cli.py's _build_parser(), plus an\nexit-code table (0/1/2) matching the actual SystemExit/return values\nin cli.py and their test coverage in tests/unit/test_cli.py.\n\nCo-authored-by: Rudrendu <RudrenduPaul@users.noreply.github.com>",
          "timestamp": "2026-07-21T19:24:25-07:00",
          "tree_id": "d5edb7a62d2d34dc14d3a01083a2ab02bcc1c223",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/395defd470abb832102b5c6ac7f28c0cd48da028"
        },
        "date": 1784687083487,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1867.631718393992,
            "unit": "iter/sec",
            "range": "stddev: 0.000041266809422867234",
            "extra": "mean: 535.4374688281246 usec\nrounds: 802"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1291.4403731872462,
            "unit": "iter/sec",
            "range": "stddev: 0.00003583375865474856",
            "extra": "mean: 774.3292069551937 usec\nrounds: 1150"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 26.470474100847795,
            "unit": "iter/sec",
            "range": "stddev: 0.00023373723417753145",
            "extra": "mean: 37.77794066665289 msec\nrounds: 27"
          }
        ]
      }
    ]
  }
}