import json

xp_needed_to_level_up_to_next_level = 100
total_xp_required_for_level = 0
incrementor = 55

# 445107400056242186
# 165 - the 95
# 164 - Human Compiler
levels = {}
level_names = {
    1: 'Hello World',
    5: 'Missing Semicolon',
    10: 'Manual Tester',
    15: 'Javascript Programmer',
    20: 'Syntax Error',
    25: 'Git Gud',
    30: 'Full Stack Developer',
    35: 'Assembly Programmer',
    40: 'Segmentation Fault',
    45: 'Vim User',
    50: 'Kernel',
    55: 'Stallman Follower',
    60: 'Forkbomb',
    65: 'Human Compiler',
    70: 'Gentoo Installer',
    75: 'HolyC',
    80: 'CD level80',
    85: 'THE 85',
    90: 'THE 90',
    95: 'THE 95'
}

for level_number in range(0, 101):
    levels[level_number] = {
        'xp_needed_to_level_up_to_next_level': xp_needed_to_level_up_to_next_level,
        'total_xp_required_for_level': total_xp_required_for_level
    }
    if level_number in level_names.keys():
        levels[level_number]['role_name'] = level_names[level_number]
    total_xp_required_for_level += xp_needed_to_level_up_to_next_level
    xp_needed_to_level_up_to_next_level += incrementor
    incrementor += 10


with open('levels.json', 'w') as f:
    json.dump(levels, f, indent=4)
