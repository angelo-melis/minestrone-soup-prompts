import sys, os, re, random, json

nspterminology = None
nspvalues = {}


def wget(url, output):
    import subprocess
    res = subprocess.run(['wget', '-q', url, '-O', output], stdout=subprocess.PIPE).stdout.decode('utf-8')
    print(res)


def pick_variant(prompt):
    if prompt is None:
        return None

    out = prompt
    variants = re.findall(r'\{[^{}]*?}', out)

    for v in variants:
        opts = v.strip("{}").split('|')
        out = out.replace(v, random.choice(opts))

    combinations = re.findall(r'\[[^\[\]]*?]', out)
    combinations_nr = 0

    for c in combinations:
        sc = c.strip("[]")
        parts = sc.split('$$')
        n_pick = None

        if len(parts) > 2:
            sys.exit(" we do not support more than 1 $$ in a combination")
        if len(parts) == 2:
            sc = parts[1]
            if parts[0] != '':
                n_pick = int(parts[0])

        if sc.startswith('@'):
            if sc[1:] in nspterminology:
                opts = nspterminology[sc[1:]]

                if not n_pick:
                    if len(parts) == 1:
                        n_pick = 1
                    else:
                        n_pick = random.randint(1, len(opts))

                sample = random.sample(opts, n_pick)
            else:
                if sc[1:] == '':
                    sys.exit("Error: empty nspterminology key!")
                else:
                    sys.exit(f"Error: {sc[1:]} not found in nspterminology")
        elif sc.startswith('%'):
            parts2 = sc[1:].split(":")

            if len(parts2) > 2:
                sys.exit("Error: we do not support more than 1 : in a %-list combo")
            elif len(parts2) == 2:
                sc2 = parts2[0]
                parts3 = parts2[1].split(",")
                if len(parts3) > 2:
                    sys.exit("Error: we do not support more than 1 , in a %-list value")
                elif len(parts3) == 2:
                    liststart = int(parts3[0])
                    listaddition = int(parts3[1])
                else:
                    liststart = int(parts3[0])
                    listaddition = 1
            else:
                sc2 = parts2[0]
                liststart = 0
                listaddition = 1

            if sc2 in nspterminology:
                sc2_key = sc2 + str(combinations_nr)
                if liststart - 1 >= len(nspterminology[sc2]):
                    liststart = 0

                if sc2_key not in nspvalues:
                    nspvalues[sc2_key] = [liststart, len(nspterminology[sc2]), listaddition]
                else:
                    liststart = nspvalues[sc2_key][0]

                if not n_pick:
                    if len(parts) == 1:
                        n_pick = 1
                    else:
                        n_pick = random.randint(1, len(nspterminology[sc2]) - liststart)

                if liststart + n_pick > nspvalues[sc2_key][1]:
                    listend = nspvalues[sc2_key][1]
                else:
                    listend = liststart + n_pick

                sample = nspterminology[sc2][liststart:listend]
                nspvalues[sc2_key][0] = nspvalues[sc2_key][0] + nspvalues[sc2_key][2]
                combinations_nr = combinations_nr + 1
            else:
                if sc2 == '':
                    sys.exit("Error: empty nspterminology key!")
                else:
                    sys.exit(f"Error: {sc2} not found in nspterminology")
        else:
            opts = sc.split('|')

            if not n_pick:
                if len(parts) == 1:
                    n_pick = 1
                else:
                    n_pick = random.randint(1, len(opts))

            sample = random.sample(opts, n_pick)

        out = out.replace(c, ', '.join(sample))

    if len(variants + combinations) > 0:
        return pick_variant(out)
    return out


def pick_prompt_variant(prompt):
    global nspterminology

    new_prompts = []
    new_dict = {}

    if not os.path.exists('./nsp_pantry.json'):
        wget('https://raw.githubusercontent.com/WASasquatch/noodle-soup-prompts/main/nsp_pantry.json',
             './nsp_pantry.json')

    if nspterminology is None:
        with open('./nsp_pantry.json', 'r') as f:
            nspterminology = json.loads(f.read())

    ptype = type(prompt)

    if ptype == dict:
        for pstep, pvalue in prompt.items():
            if type(pvalue) == list:
                for prompt in pvalue:
                    new_prompt = pick_variant(prompt)
                    new_prompts.append(new_prompt)
                new_dict[pstep] = new_prompts
                new_prompts = []
        return new_dict
    elif ptype == list:
        for pstr in prompt:
            new_prompt = pick_variant(pstr)
            new_prompts.append(new_prompt)
            new_prompt = None
        return new_prompts
    elif ptype == str:
        new_prompt = pick_variant(prompt)
        return new_prompt
    else:
        return


def nsp_parse(prompt):
    return pick_prompt_variant(prompt)
