window.BENCHMARK_DATA = {
  "lastUpdate": 1785716255663,
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
          "id": "f677652423b05362c90b34f64918b30904ed0a4e",
          "message": "Rename npm package from agent-regress-npm-cli to agent-regress-cli (#14)\n\nMatches the PyPI package name and the portfolio-wide convention of\nidentical names across registries -- the '-npm-' insertion was the\none cross-registry naming inconsistency found in a portfolio-wide\naudit. The old name will be deprecated pointing at this one once the\nnew name is published.\n\nCo-authored-by: Rudrendu <RudrenduPaul@users.noreply.github.com>",
          "timestamp": "2026-07-21T19:58:24-07:00",
          "tree_id": "ce202e00c017c0ec0b2c25674bc0bbe87e0fdb76",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/f677652423b05362c90b34f64918b30904ed0a4e"
        },
        "date": 1784689122095,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2250.5137056538333,
            "unit": "iter/sec",
            "range": "stddev: 0.00004340354052614739",
            "extra": "mean: 444.3429948850162 usec\nrounds: 782"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1489.2484227590978,
            "unit": "iter/sec",
            "range": "stddev: 0.000021792019905588006",
            "extra": "mean: 671.4796435018692 usec\nrounds: 1108"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.64428767862657,
            "unit": "iter/sec",
            "range": "stddev: 0.0002473507446450204",
            "extra": "mean: 40.57735459999833 msec\nrounds: 25"
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
          "id": "e5fb67cd770a9d6c4e184f7f97f6ab1b0a2100cd",
          "message": "Add missing PyPI Environment classifier (#15)\n\nCo-authored-by: Rudrendu <RudrenduPaul@users.noreply.github.com>",
          "timestamp": "2026-07-21T20:03:58-07:00",
          "tree_id": "e2f2f28b4eb5b005e2b1c3d17f1b4a354949040f",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/e5fb67cd770a9d6c4e184f7f97f6ab1b0a2100cd"
        },
        "date": 1784689682612,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2684.5599400585616,
            "unit": "iter/sec",
            "range": "stddev: 0.000026327161577905017",
            "extra": "mean: 372.5005298180028 usec\nrounds: 872"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1743.607668698145,
            "unit": "iter/sec",
            "range": "stddev: 0.00004483579745639276",
            "extra": "mean: 573.5235156121128 usec\nrounds: 1313"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 38.73963187747264,
            "unit": "iter/sec",
            "range": "stddev: 0.0006791611890995603",
            "extra": "mean: 25.813358349992654 msec\nrounds: 40"
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
          "id": "8ace1afcea4bde98c2bcfb15770b824623d21ec8",
          "message": "Merge remote-tracking branch 'origin/main'\n\n# Conflicts:\n#\tREADME.md\n#\tdocs/assets/demo-2-p0-crash.gif\n#\tdocs/assets/demo-3-cli.gif\n#\tnpm/README.md\n#\tnpm/bin/agent-regress.js\n#\tnpm/package.json\n#\tpyproject.toml\n#\tuv.lock",
          "timestamp": "2026-08-02T17:13:49-07:00",
          "tree_id": "205e9b786926c2075075de1b5f1c04cbebb50b2c",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/8ace1afcea4bde98c2bcfb15770b824623d21ec8"
        },
        "date": 1785716054708,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1860.2647177887854,
            "unit": "iter/sec",
            "range": "stddev: 0.000022913530431061747",
            "extra": "mean: 537.5579026132667 usec\nrounds: 842"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1287.2061370861716,
            "unit": "iter/sec",
            "range": "stddev: 0.00002829644583579483",
            "extra": "mean: 776.876345744967 usec\nrounds: 1128"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.785156236276745,
            "unit": "iter/sec",
            "range": "stddev: 0.000567365537116612",
            "extra": "mean: 40.34672973077136 msec\nrounds: 26"
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
          "id": "1bbca70db7d0bc0dee432b7b21cdd7935c2926eb",
          "message": "Merge pull request #21 from RudrenduPaul/dependabot/github_actions/benchmark-action/github-action-benchmark-1.22.1\n\nchore(deps): bump benchmark-action/github-action-benchmark from 1.20.4 to 1.22.1",
          "timestamp": "2026-08-02T17:15:21-07:00",
          "tree_id": "5f5729d4f97bf2000c9e94073908ff7856293413",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/1bbca70db7d0bc0dee432b7b21cdd7935c2926eb"
        },
        "date": 1785716138642,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 3319.502874181515,
            "unit": "iter/sec",
            "range": "stddev: 0.000020859512089569535",
            "extra": "mean: 301.2499274448041 usec\nrounds: 951"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 2157.8606455623185,
            "unit": "iter/sec",
            "range": "stddev: 0.000014117926830904747",
            "extra": "mean: 463.42195547081275 usec\nrounds: 1572"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 48.68876263537258,
            "unit": "iter/sec",
            "range": "stddev: 0.00022265519165435194",
            "extra": "mean: 20.53862012244887 msec\nrounds: 49"
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
          "id": "2baa97abe4c6bb1a3edbefe14601429cd6a73d81",
          "message": "Merge pull request #26 from RudrenduPaul/fix/remove-old-npm-name-refs\n\nRemove remaining literal references to the old npm package name",
          "timestamp": "2026-08-02T17:15:18-07:00",
          "tree_id": "9a62e8c55b2b679a80a8207b931cfeae77caef66",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/2baa97abe4c6bb1a3edbefe14601429cd6a73d81"
        },
        "date": 1785716142200,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2279.531997118842,
            "unit": "iter/sec",
            "range": "stddev: 0.00001907227379350888",
            "extra": "mean: 438.6865379665322 usec\nrounds: 777"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1492.9770797282158,
            "unit": "iter/sec",
            "range": "stddev: 0.00002062351285287793",
            "extra": "mean: 669.8026470587491 usec\nrounds: 1122"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.70317513924353,
            "unit": "iter/sec",
            "range": "stddev: 0.00029059655056022047",
            "extra": "mean: 40.48062624999963 msec\nrounds: 24"
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
          "id": "7658d48ffa3fa0dac59c3802c5959a14231c6ca7",
          "message": "Merge pull request #20 from RudrenduPaul/dependabot/github_actions/softprops/action-gh-release-3.0.2\n\nchore(deps): bump softprops/action-gh-release from 3.0.1 to 3.0.2",
          "timestamp": "2026-08-02T17:15:24-07:00",
          "tree_id": "f42715b28c7483416b032f4b8421f1748de101be",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/7658d48ffa3fa0dac59c3802c5959a14231c6ca7"
        },
        "date": 1785716143275,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2986.6332208733306,
            "unit": "iter/sec",
            "range": "stddev: 0.000013585412359159271",
            "extra": "mean: 334.8251780670902 usec\nrounds: 921"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1986.122666286251,
            "unit": "iter/sec",
            "range": "stddev: 0.0000158984228017396",
            "extra": "mean: 503.4935741757828 usec\nrounds: 1456"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 32.29279672112908,
            "unit": "iter/sec",
            "range": "stddev: 0.0007262628293745777",
            "extra": "mean: 30.966658250002332 msec\nrounds: 32"
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
          "id": "814dd2a9cd9536e22d275bbac00fed3dcbd7b998",
          "message": "Merge pull request #19 from RudrenduPaul/dependabot/github_actions/ossf/scorecard-action-2.4.4\n\nchore(deps): bump ossf/scorecard-action from 2.4.3 to 2.4.4",
          "timestamp": "2026-08-02T17:15:27-07:00",
          "tree_id": "26bbd803faa8186e65b3f31dd91297116593fe74",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/814dd2a9cd9536e22d275bbac00fed3dcbd7b998"
        },
        "date": 1785716145801,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2553.1968150239154,
            "unit": "iter/sec",
            "range": "stddev: 0.00003799881376317474",
            "extra": "mean: 391.66584969699375 usec\nrounds: 825"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1781.3483468724824,
            "unit": "iter/sec",
            "range": "stddev: 0.000021006457443160972",
            "extra": "mean: 561.3725141158957 usec\nrounds: 1346"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 37.66855856594929,
            "unit": "iter/sec",
            "range": "stddev: 0.000367384528186007",
            "extra": "mean: 26.54733916216151 msec\nrounds: 37"
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
          "id": "6abad395a31c73df49ed3b6ce9b1ee883d0e24d2",
          "message": "Merge pull request #17 from RudrenduPaul/dependabot/github_actions/astral-sh/setup-uv-9.0.0\n\nchore(deps): bump astral-sh/setup-uv from 7.6.0 to 9.0.0",
          "timestamp": "2026-08-02T17:15:29-07:00",
          "tree_id": "41e75339b911d221ff3171c467ead59466a3647c",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/6abad395a31c73df49ed3b6ce9b1ee883d0e24d2"
        },
        "date": 1785716148362,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2277.9076171987313,
            "unit": "iter/sec",
            "range": "stddev: 0.00001832761001601623",
            "extra": "mean: 438.9993661067586 usec\nrounds: 773"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1501.9126058994964,
            "unit": "iter/sec",
            "range": "stddev: 0.00002005559156124868",
            "extra": "mean: 665.8177020899957 usec\nrounds: 1148"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.66084387776144,
            "unit": "iter/sec",
            "range": "stddev: 0.00032911565232949256",
            "extra": "mean: 40.55011276000073 msec\nrounds: 25"
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
          "id": "2e251f804e1ba862a881ef688b27cdd4c4f3a862",
          "message": "Bump github/codeql-action to v4.37.3 across all steps\n\nDependabot PR #18 only bumped the analyze step, leaving init/autobuild/\nupload-sarif pinned to v4.37.0. CodeQL requires all steps in a job to\nshare the same config version, which broke the CodeQL Security Analysis\ncheck with a 'configuration error'.",
          "timestamp": "2026-08-02T17:17:13-07:00",
          "tree_id": "515ff9220374d16867c5e996e932c9b9a7927927",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/2e251f804e1ba862a881ef688b27cdd4c4f3a862"
        },
        "date": 1785716255265,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 3056.5414235212556,
            "unit": "iter/sec",
            "range": "stddev: 0.000014268532281224307",
            "extra": "mean: 327.1671675393036 usec\nrounds: 955"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 2012.7116321951403,
            "unit": "iter/sec",
            "range": "stddev: 0.00001650268679849455",
            "extra": "mean: 496.8421625850901 usec\nrounds: 1470"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 31.107642768802005,
            "unit": "iter/sec",
            "range": "stddev: 0.0009301086514006332",
            "extra": "mean: 32.146440906249076 msec\nrounds: 32"
          }
        ]
      }
    ]
  }
}