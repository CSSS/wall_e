
```shell
jace@wall-e:~$ docker ps
CONTAINER ID        IMAGE               COMMAND              CREATED             STATUS              PORTS               NAMES
b1a734e6bd79        wall-e:3            "python ./main.py"   5 hours ago         Up 5 hours                              wall-e-test-PR-54
b546d702cded        86f556a22552        "python ./main.py"   5 hours ago         Up 5 hours                              wall-e-test-PR-56
3aaa03aa3ee6        wall-e:34           "python ./main.py"   5 hours ago         Up 5 hours                              wall-e
3f0175319719        wall-e:34           "python ./main.py"   5 hours ago         Up 5 hours                              wall-e-test-master
c4219fbd2cb2        wall-e:1            "python ./main.py"   6 hours ago         Up 6 hours                              wall-e-test-fix_issue_with_logging
3addde3f3ff2        1c6ebb8370bd        "python ./main.py"   11 hours ago        Up 11 hours                             wall-e-test-PR-53
957b4f2dc686        wall-e:6            "python ./main.py"   12 hours ago        Up 12 hours                             wall-e-test-adding_roles_command
e63cbd648214        fcb3d956f789        "python ./main.py"   47 hours ago        Up 47 hours                             wall-e-test-improving_json_output
dcd218ea8388        2964fda04b35        "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-PR-52
8cdcf79d45e0        wall-e:5            "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-modernNeo-patch-1
f72397190354        wall-e:7            "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-PR-51
6a7e4128f44a        3ac7def8e5f2        "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-add_reminder_commands
ecd0af2f5e59        a3d96c94c56a        "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-delete_reminder
9fbeb76f6354        7c310300db29        "python ./main.py"   2 days ago          Up 2 days                               wall-e-test-welcome_message
```

```shell
docker exec -it <NAME> ash
```

```shell
docker logs <NAME>
```