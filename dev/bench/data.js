window.BENCHMARK_DATA = {
  "lastUpdate": 1786394248276,
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
          "id": "ed19d6f1a409137f1f74314d8cc85b05283c162d",
          "message": "Prevent uv run from re-dirtying uv.lock in Benchmark workflow\n\nuv run performs its own implicit sync before executing, which was\nstill rewriting uv.lock even after 'uv sync --frozen'. Freeze the\nrun step too and discard any residual drift before the gh-pages\nbranch switch as a safety net.",
          "timestamp": "2026-08-03T15:03:58-07:00",
          "tree_id": "3595fbb6021183571f5a75e664cba98de5ebc949",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/ed19d6f1a409137f1f74314d8cc85b05283c162d"
        },
        "date": 1785794659847,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 3063.8088102867864,
            "unit": "iter/sec",
            "range": "stddev: 0.00001405469136522667",
            "extra": "mean: 326.3911235722295 usec\nrounds: 963"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 2023.955705180127,
            "unit": "iter/sec",
            "range": "stddev: 0.00001883981413971979",
            "extra": "mean: 494.08195912617686 usec\nrounds: 1419"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 32.908999053386864,
            "unit": "iter/sec",
            "range": "stddev: 0.0011762739266931747",
            "extra": "mean: 30.386825147059096 msec\nrounds: 34"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "49699333+dependabot[bot]@users.noreply.github.com",
            "name": "dependabot[bot]",
            "username": "dependabot[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "8a8cef64ef583edb0b9b9673db4e24c8d188e42b",
          "message": "chore(deps): bump cryptography from 49.0.0 to 50.0.0 (#28)\n\nBumps [cryptography](https://github.com/pyca/cryptography) from 49.0.0 to 50.0.0.\n- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)\n- [Commits](https://github.com/pyca/cryptography/compare/49.0.0...50.0.0)\n\n---\nupdated-dependencies:\n- dependency-name: cryptography\n  dependency-version: 50.0.0\n  dependency-type: indirect\n...\n\nSigned-off-by: dependabot[bot] <support@github.com>\nCo-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
          "timestamp": "2026-08-03T15:04:43-07:00",
          "tree_id": "4ee4af77154efe792b490d74820cf69364d7b129",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/8a8cef64ef583edb0b9b9673db4e24c8d188e42b"
        },
        "date": 1785794701265,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2280.5502860986226,
            "unit": "iter/sec",
            "range": "stddev: 0.00001985330698410153",
            "extra": "mean: 438.4906599497604 usec\nrounds: 794"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1495.5020350608088,
            "unit": "iter/sec",
            "range": "stddev: 0.000020169429413043866",
            "extra": "mean: 668.6717747992492 usec\nrounds: 1119"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.84340808124953,
            "unit": "iter/sec",
            "range": "stddev: 0.0015121231466091948",
            "extra": "mean: 40.25212630769231 msec\nrounds: 26"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "49699333+dependabot[bot]@users.noreply.github.com",
            "name": "dependabot[bot]",
            "username": "dependabot[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "82920c1ab14a012047632178995bcf1511047a73",
          "message": "chore(deps): bump aiohttp from 3.14.1 to 3.14.3 (#29)\n\nBumps [aiohttp](https://github.com/aio-libs/aiohttp) from 3.14.1 to 3.14.3.\n- [Changelog](https://github.com/aio-libs/aiohttp/blob/master/CHANGES.rst)\n- [Commits](https://github.com/aio-libs/aiohttp/compare/v3.14.1...v3.14.3)\n\n---\nupdated-dependencies:\n- dependency-name: aiohttp\n  dependency-version: 3.14.3\n  dependency-type: indirect\n...\n\nSigned-off-by: dependabot[bot] <support@github.com>\nCo-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
          "timestamp": "2026-08-03T15:04:46-07:00",
          "tree_id": "2e6cc4ac6e1cfe9454d6cc95fa09dd26d8870ea6",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/82920c1ab14a012047632178995bcf1511047a73"
        },
        "date": 1785794703749,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1848.5245203936356,
            "unit": "iter/sec",
            "range": "stddev: 0.000024509686961862963",
            "extra": "mean: 540.971996296297 usec\nrounds: 810"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1288.9981207973708,
            "unit": "iter/sec",
            "range": "stddev: 0.00002014304139509111",
            "extra": "mean: 775.796321084939 usec\nrounds: 1143"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.209827185073184,
            "unit": "iter/sec",
            "range": "stddev: 0.004228939033818822",
            "extra": "mean: 39.66707080769292 msec\nrounds: 26"
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
          "id": "5c0e09a1123ab4ece3f7eb3a7af25d3d67e7ee31",
          "message": "Make all demo GIFs consistent in dimensions",
          "timestamp": "2026-08-09T00:02:19-07:00",
          "tree_id": "24fdc4649025b4d9f7baa735f3598db778522128",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/5c0e09a1123ab4ece3f7eb3a7af25d3d67e7ee31"
        },
        "date": 1786258964098,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1920.039919920224,
            "unit": "iter/sec",
            "range": "stddev: 0.000018709004945603155",
            "extra": "mean: 520.8225045870656 usec\nrounds: 872"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1320.5574435668664,
            "unit": "iter/sec",
            "range": "stddev: 0.0000160452291965501",
            "extra": "mean: 757.2559640411924 usec\nrounds: 1168"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.74795047682759,
            "unit": "iter/sec",
            "range": "stddev: 0.0007868167463764477",
            "extra": "mean: 40.40738649999872 msec\nrounds: 26"
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
          "id": "adaa28e62438529f33d2e25269bc66dcb25afbab",
          "message": "Re-record demo GIFs to remove leaked local username/path\n\nBoth demo-1-comparison.gif and demo-2-p0-crash.gif were recorded from the\nreal maintainer machine and leaked the absolute macOS path (including the\nreal username) in typed commands and, in demo-2, a full Python traceback.\nRe-recorded from a generic clone path with a real reproduced AttributeError\nfrom the current openai-agents SDK, same content/narrative, same 900x560\ndimensions.",
          "timestamp": "2026-08-09T01:07:49-07:00",
          "tree_id": "3c0b3934651fc652d1cb7cd5d7f904fb8d652325",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/adaa28e62438529f33d2e25269bc66dcb25afbab"
        },
        "date": 1786262895757,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1822.0290235338312,
            "unit": "iter/sec",
            "range": "stddev: 0.00003451450212469463",
            "extra": "mean: 548.838677695977 usec\nrounds: 816"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1268.9006473828654,
            "unit": "iter/sec",
            "range": "stddev: 0.000030273196473919223",
            "extra": "mean: 788.0837653148978 usec\nrounds: 1159"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.189754420045723,
            "unit": "iter/sec",
            "range": "stddev: 0.0005335556813989877",
            "extra": "mean: 39.69868000000076 msec\nrounds: 25"
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
          "id": "81b7ce6fcefc785f806ef784677f7d42137cbbdd",
          "message": "Add remaining demo GIFs to README",
          "timestamp": "2026-08-09T02:09:12-07:00",
          "tree_id": "10e0e535551c4488e40d52d9a29d495d0d3f7211",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/81b7ce6fcefc785f806ef784677f7d42137cbbdd"
        },
        "date": 1786266574375,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2286.887133714344,
            "unit": "iter/sec",
            "range": "stddev: 0.000022217799610425318",
            "extra": "mean: 437.2756246941701 usec\nrounds: 818"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1499.5025457318736,
            "unit": "iter/sec",
            "range": "stddev: 0.000021786086785010213",
            "extra": "mean: 666.8878307985282 usec\nrounds: 1117"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.38661981282419,
            "unit": "iter/sec",
            "range": "stddev: 0.00027343344546577317",
            "extra": "mean: 41.00609299998723 msec\nrounds: 25"
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
          "id": "a6a559d64a11bb77b29ae192590b69b7059aeded",
          "message": "Update demo GIFs with richer, PH-quality recordings",
          "timestamp": "2026-08-09T11:32:45-07:00",
          "tree_id": "e12567d2559e27fe57f9774c65fcce5b4e86ca4c",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/a6a559d64a11bb77b29ae192590b69b7059aeded"
        },
        "date": 1786300384750,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2296.1162160081217,
            "unit": "iter/sec",
            "range": "stddev: 0.000020086246770702834",
            "extra": "mean: 435.5180251888708 usec\nrounds: 794"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1504.0156101953105,
            "unit": "iter/sec",
            "range": "stddev: 0.000019693805988779762",
            "extra": "mean: 664.886716082781 usec\nrounds: 1113"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.39222900152859,
            "unit": "iter/sec",
            "range": "stddev: 0.00041056378229324176",
            "extra": "mean: 40.9966633199997 msec\nrounds: 25"
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
          "id": "d098aeb35adb3b641c92ef782b33a78d717c913a",
          "message": "Add traffic-light window dots to demo GIFs",
          "timestamp": "2026-08-09T12:06:25-07:00",
          "tree_id": "f1933ab654cbef51e1ac15ab5713d03342e343c6",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/d098aeb35adb3b641c92ef782b33a78d717c913a"
        },
        "date": 1786302412969,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2292.4901805321383,
            "unit": "iter/sec",
            "range": "stddev: 0.00001919625180550378",
            "extra": "mean: 436.20688476313455 usec\nrounds: 781"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1488.308755192455,
            "unit": "iter/sec",
            "range": "stddev: 0.000021519439140640662",
            "extra": "mean: 671.9035929279935 usec\nrounds: 1103"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.323488599564946,
            "unit": "iter/sec",
            "range": "stddev: 0.00046334864643174573",
            "extra": "mean: 39.489029960002426 msec\nrounds: 25"
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
          "id": "7e8d30cae216797488705e3e7830a87dc8e0ae8b",
          "message": "Fix demo GIF file size (was bloated after a recent edit)",
          "timestamp": "2026-08-09T12:18:26-07:00",
          "tree_id": "a23df4d0537b98ed5900ad4ab2e489737c8332f8",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/7e8d30cae216797488705e3e7830a87dc8e0ae8b"
        },
        "date": 1786303131914,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2152.973260224869,
            "unit": "iter/sec",
            "range": "stddev: 0.000018515856112106857",
            "extra": "mean: 464.4739525912896 usec\nrounds: 907"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1439.0307919747713,
            "unit": "iter/sec",
            "range": "stddev: 0.000026245734875028428",
            "extra": "mean: 694.9121628090442 usec\nrounds: 1253"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 29.751093810617263,
            "unit": "iter/sec",
            "range": "stddev: 0.000691225230907964",
            "extra": "mean: 33.61220956666576 msec\nrounds: 30"
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
          "id": "3b1bd50c53dafbb8e4345ff1ede8c989d933e80f",
          "message": "Move demo GIF above the fold for engagement",
          "timestamp": "2026-08-09T12:34:48-07:00",
          "tree_id": "dc83abb620219ebcccf8becbf95219dca0b79401",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/3b1bd50c53dafbb8e4345ff1ede8c989d933e80f"
        },
        "date": 1786304107913,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1854.979366027384,
            "unit": "iter/sec",
            "range": "stddev: 0.00002633355743469651",
            "extra": "mean: 539.0895544793018 usec\nrounds: 826"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1257.9070474042778,
            "unit": "iter/sec",
            "range": "stddev: 0.00011165941727825391",
            "extra": "mean: 794.9712994004801 usec\nrounds: 1169"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.89887620217013,
            "unit": "iter/sec",
            "range": "stddev: 0.0006323624820069183",
            "extra": "mean: 40.16245519999984 msec\nrounds: 25"
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
          "id": "029a8241ac206fc5f40e0442ad57a0db730a1d1f",
          "message": "Add CodeQL security scanning workflow",
          "timestamp": "2026-08-09T12:44:56-07:00",
          "tree_id": "5997c7741cf494aeef6418396ebcceae897091ed",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/029a8241ac206fc5f40e0442ad57a0db730a1d1f"
        },
        "date": 1786304754272,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 2336.6495749742735,
            "unit": "iter/sec",
            "range": "stddev: 0.000021454823502797575",
            "extra": "mean: 427.9631874244601 usec\nrounds: 827"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1554.1954016397776,
            "unit": "iter/sec",
            "range": "stddev: 0.000022012474713779115",
            "extra": "mean: 643.4197392071387 usec\nrounds: 1135"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 32.80968019043122,
            "unit": "iter/sec",
            "range": "stddev: 0.0009786109922003108",
            "extra": "mean: 30.478809735294064 msec\nrounds: 34"
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
          "id": "76bb32d90196aa63414817e12017693e1f0045a7",
          "message": "Improve README structure and searchability per portfolio design study",
          "timestamp": "2026-08-09T15:16:39-07:00",
          "tree_id": "869c68a7fe549580985f2177882d40ab09620b91",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/76bb32d90196aa63414817e12017693e1f0045a7"
        },
        "date": 1786313830746,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1863.9238164394956,
            "unit": "iter/sec",
            "range": "stddev: 0.000018886620679570598",
            "extra": "mean: 536.5026140983701 usec\nrounds: 837"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1290.5957721822758,
            "unit": "iter/sec",
            "range": "stddev: 0.000018544415531669045",
            "extra": "mean: 774.8359490664488 usec\nrounds: 1178"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 25.672620382993546,
            "unit": "iter/sec",
            "range": "stddev: 0.0003780554979900898",
            "extra": "mean: 38.9520035384637 msec\nrounds: 26"
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
          "id": "1ea8192b2cf508fa4a781cf133dabd759ce53bb4",
          "message": "Add MCP server wrapper, publish to MCP Registry\n\nExposes the agent-regress CLI as a stdio MCP tool via the mcp[cli]\noptional dependency group. Adds the registry ownership-proof string\nto README.md for registry.modelcontextprotocol.io publishing.",
          "timestamp": "2026-08-10T13:18:16-07:00",
          "tree_id": "32147d396dd151568f027dd866cfb59b928711ff",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/1ea8192b2cf508fa4a781cf133dabd759ce53bb4"
        },
        "date": 1786393122049,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1870.5823307306048,
            "unit": "iter/sec",
            "range": "stddev: 0.000032645551860802204",
            "extra": "mean: 534.5928824257759 usec\nrounds: 808"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1289.5901259937357,
            "unit": "iter/sec",
            "range": "stddev: 0.000026853053343866557",
            "extra": "mean: 775.4401804444784 usec\nrounds: 1125"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.2043402591704,
            "unit": "iter/sec",
            "range": "stddev: 0.0007974819189417632",
            "extra": "mean: 41.31490423999992 msec\nrounds: 25"
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
          "id": "4e4604f9485d80eaf5970321f64d9e3117900521",
          "message": "Add server.json for MCP Registry publishing",
          "timestamp": "2026-08-10T13:37:06-07:00",
          "tree_id": "7dde41464806b06dc74b6831af83c1bba3c8a2fa",
          "url": "https://github.com/RudrenduPaul/agent-eval/commit/4e4604f9485d80eaf5970321f64d9e3117900521"
        },
        "date": 1786394247538,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n50",
            "value": 1880.1655842257394,
            "unit": "iter/sec",
            "range": "stddev: 0.00002038075135525438",
            "extra": "mean: 531.8680484260669 usec\nrounds: 826"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_mann_whitney_n1000",
            "value": 1303.1685082320425,
            "unit": "iter/sec",
            "range": "stddev: 0.000017795706831157777",
            "extra": "mean: 767.360470793344 usec\nrounds: 1147"
          },
          {
            "name": "benchmarks/test_stat_overhead.py::test_bootstrap_n1000",
            "value": 24.712737006434807,
            "unit": "iter/sec",
            "range": "stddev: 0.0004349158712312759",
            "extra": "mean: 40.46496346153871 msec\nrounds: 26"
          }
        ]
      }
    ]
  }
}