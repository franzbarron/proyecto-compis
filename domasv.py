import sys
import json


class Memory:
    def __init__(self, i, f, s, b):
        self.ints = [None] * int(i)
        self.floats = [None] * int(f)
        self.strings = [None] * int(s)
        self.bools = [None] * int(b)

    def insert_ints(self, arr_ints):
        for idx, values in enumerate(arr_ints):
            self.ints[idx] = int(values)

    def insert_floats(self, arr_floats):
        for idx, values in enumerate(arr_floats):
            self.floats[idx] = float(values)

    def insert_strings(self, arr_string):
        for idx, values in enumerate(arr_string):
            self.strings[idx] = values

    def insert_bools(self, arr_bools):
        for idx, values in enumerate(arr_bools):
            self.bools[idx] = values == 'true'

    def get_value_of_address(self, address):
        if address < 300:
            return int(self.ints[address])
        elif address < 600:
            return self.floats[address % 300]
        elif address < 900:
            return self.strings[address % 300]
        else:
            return self.bools[address % 300]

    def set_value_in_address(self, address, value):
        if address < 300:
            self.ints[address] = value
        elif address < 600:
            self.floats[address % 300] = value
        elif address < 900:
            self.strings[address % 300] = value
        else:
            self.bools[address % 300] = value

    def set_param_value_in_addres(self, value, type):
        if type == '0':
            idx = next(idx for idx, item in enumerate(
                self.ints) if item is None)
            self.ints[idx] = value
        elif type == '1':
            idx = next(idx for idx, item in enumerate(
                self.floats) if item is None)
            self.floats[idx] = value
        elif type == '2':
            idx = next(idx for idx, item in enumerate(
                self.strings) if item is None)
            self.strings[idx] = value
        else:
            idx = next(idx for idx, item in enumerate(
                self.bools) if item is None)
            self.bools[idx] = value


func_dir = {}
class_dir = {}
ip = 1
local_mems = []
temp_mems = []
global_mem = None
constants_mem = None
aux_loc_mem = None
aux_temp_mem = None
next_func = None
ip_stack = []
read_values_stack = []
class_mem = None


def reconstruct_func_dir(line):
    name, _rt, num_types, params, num_temps, start, *_ = line.split(' ')
    if name == 'main':
        func_dir[name] = {'num_types': num_types, 'num_temps': num_temps}
    else:
        func_dir[name] = {'num_types': num_types,
                          'num_temps': num_temps, 'start': start, 'params': params}


def reconstruct_class_dir(line, class_name):
    name, _rt, num_types, _params, start, *_ = line.split(' ')
    class_dir[class_name][name] = {'num_types': num_types, 'start': start}


def initialize_constant_mem(infile):
    _, *values = infile.readline().rstrip('\n').split('\u001f')
    ints = values[0:-1]
    _, *values = infile.readline().rstrip('\n').split('\u001f')
    floats = values[0:-1]
    _, *values = infile.readline().rstrip('\n').split('\u001f')
    strings = values[0:-1]
    _, *values = infile.readline().rstrip('\n').split('\u001f')
    bools = values[0:-1]
    constants_mem = Memory(len(ints), len(
        floats), len(strings), len(bools))
    constants_mem.insert_ints(ints)
    constants_mem.insert_floats(floats)
    constants_mem.insert_strings(strings)
    constants_mem.insert_bools(bools)
    return constants_mem


def get_actual_value(address):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }
    if int(address) >= 6000:
        prev_local_mem = local_mems[-2]
        addr = class_mem.get_value_of_address(int(address) % 1500)
        if int(addr) // 1500 == 1:
            val = prev_local_mem.get_value_of_address(
                int(addr) % 1500)
        else:
            val = memories[str(int(address) // 1500)
                           ].get_value_of_address(int(addr) % 1500)
    else:
        val = memories[str(int(address) // 1500)
                       ].get_value_of_address(int(address) % 1500)

    return val


def do_addition(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }
    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    sum_res = left_dir_val + right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, sum_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, sum_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, sum_res)


def do_multiplication(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val * right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def do_subtraction(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val - right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def do_division(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }
    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val / right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_gt(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val > right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_lt(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val < right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_eq(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }
    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val == right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_ne(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val != right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_geq(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val >= right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def compare_leq(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val <= right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def do_or(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '4': class_mem
    }
    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val or right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def do_and(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }

    left_dir_val = get_actual_value(left)
    right_dir_val = get_actual_value(right)

    if left_dir_val == None or right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    mult_res = left_dir_val and right_dir_val

    if int(res) >= 6000:
        prev_local_mem = local_mems[-2]
        res = class_mem.get_value_of_address(int(res) % 1500)
        mem = int(res) // 1500
        if mem == 1:
            prev_local_mem.set_value_in_address(int(res) %
                                                1500, mult_res)
        else:
            memories[str(mem)].set_value_in_address(int(res) %
                                                    1500, mult_res)
    else:
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, mult_res)


def do_goto(_, __, res):
    global ip
    ip = int(res)


def do_assignment(left, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem,
        '4': class_mem
    }
    if int(res) >= 6000:
        if int(right) == -1:
            left_dir_val = memories[str(int(left) // 1500)
                                    ].get_value_of_address(int(left) % 1500)
            if left_dir_val == None:
                raise ReferenceError("Value in variable has not been assigned")
            prev_local_mem = local_mems[-2]
            res = class_mem.get_value_of_address(int(res) % 1500)
            mem = int(res) // 1500
            if mem == 1:
                prev_local_mem.set_value_in_address(int(res) %
                                                    1500, left_dir_val)
            else:
                memories[str(mem)].set_value_in_address(int(res) %
                                                        1500, left_dir_val)
        else:
            class_mem.set_value_in_address(int(res) %
                                           1500, int(left))
    else:
        left_dir_val = memories[str(int(left) // 1500)
                                ].get_value_of_address(int(left) % 1500)
        memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                             1500, left_dir_val)


def do_goto_f(_, right, res):
    global ip
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    right_dir_val = memories[str(int(right) // 1500)
                             ].get_value_of_address(int(right) % 1500)

    if right_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    ip = int(res) if right_dir_val == False else ip + 1


def do_gosub(left, _, __):
    global ip, local_mems, temp_mems, ip_stack
    local_mems.append(aux_loc_mem)
    temp_mems.append(aux_temp_mem)
    if len(local_mems) > 25:
        print('Stack overflow')
        exit(1)
    ip_stack.append(ip)
    ip = int(func_dir[left]['start'])


def do_era(left, _, __):
    global aux_loc_mem, aux_temp_mem, next_func, class_mem
    left_split = left.split('.')
    next_func = left
    ints, floats, strings, bools, _voids, * \
        _ = func_dir[left]['num_types'].split('\u001f')
    aux_loc_mem = Memory(ints, floats, strings, bools)
    ints, floats, strings, bools, _voids, * \
        _ = func_dir[left]['num_temps'].split('\u001f')
    aux_temp_mem = Memory(ints, floats, strings, bools)
    if len(left_split) > 1:
        ints, floats, strings, bools, _voids, * \
            _ = class_dir[left_split[0]]['num_types'].split('\u001f')
        class_mem = Memory(ints, floats, strings, bools)
    # print(json.dumps(class_dir, indent=2))
    # ints, floats, strings, bools, _voids, *_ = class_dir


def do_param(left, _, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    left_dir_val = memories[str(int(left) // 1500)
                            ].get_value_of_address(int(left) % 1500)

    if left_dir_val == None:
        raise ReferenceError("Value in variable has not been assigned")

    param_type = func_dir[next_func]['params'][int(res)]
    aux_loc_mem.set_param_value_in_addres(left_dir_val, param_type)


def do_print(_, __, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    res_dir_val = memories[str(int(res) // 1500)
                           ].get_value_of_address(int(res) % 1500)
    if isinstance(res_dir_val, str):
        s = str.split(res_dir_val, '\\n')
        for i in range(len(s) - 1):
            sys.stdout.write(s[i] + '\n')
        if s[-1] == '':
            sys.stdout.write(s[-1])
        else:
            sys.stdout.write(s[-1] + ' ')
    else:
        sys.stdout.write(str(res_dir_val) + ' ')


def do_endfunc(_, __, ___):
    global ip, local_mems, temp_mems, ip_stack
    local_mems.pop()
    temp_mems.pop()
    ip = ip_stack.pop()


def do_return(left, _, res):
    global ip, local_mems, temp_mems, ip_stack
    do_assignment(left, _, res)
    local_mems.pop()
    temp_mems.pop()
    ip = ip_stack.pop()


def do_end(_, __, ___):
    exit(0)


def do_read(_, __, res):
    if len(read_values_stack) == 0:
        in_line = sys.stdin.readline().rstrip('\n')
        if int(res) % 1500 < 600 or int(res) % 1500 >= 900:
            read_values_stack.extend(in_line.split(' '))
        else:
            read_values_stack.append(in_line)

    raw_val = read_values_stack.pop(0)

    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    try:
        if int(res) % 1500 < 300:
            val = int(raw_val)
            memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                                 1500, val)
        elif int(res) % 1500 < 600:
            val = float(raw_val)
            memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                                 1500, val)
        elif int(res) % 1500 < 900:
            val = str(raw_val)
            memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                                 1500, val)
        elif int(res) % 1500 < 1200:
            val = bool(raw_val)
            memories[str(int(res) // 1500)].set_value_in_address(int(res) %
                                                                 1500, val)
    except Exception as e:
        print(e)


def do_verify(_, right, res):
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    res_dir_val = memories[str(int(res) // 1500)
                           ].get_value_of_address(int(res) % 1500)
    if res_dir_val < 0 or res_dir_val >= int(right):
        raise IndexError('Index out of range')


def check_if_address(val):
    if not '$' in val:
        return val
    local_mem = local_mems[-1]
    temp_mem = temp_mems[-1]
    memories = {
        '0': global_mem,
        '1': local_mem,
        '2': temp_mem,
        '3': constants_mem
    }
    return memories[str(int(val[1:]) // 1500)
                    ].get_value_of_address(int(val[1:]) % 1500)


def run_quad(op, left, right, res):
    global ip
    operations = {
        '+': do_addition,
        '-': do_subtraction,
        '*': do_multiplication,
        '/': do_division,
        '=': do_assignment,
        '<': compare_lt,
        '>': compare_gt,
        '==': compare_eq,
        '<>': compare_ne,
        '<=': compare_leq,
        '>=': compare_geq,
        '|': do_or,
        '&': do_and,
        'goto': do_goto,
        'goto_f': do_goto_f,
        'print': do_print,
        'read': do_read,
        'gosub': do_gosub,
        'era': do_era,
        'param': do_param,
        'end_func': do_endfunc,
        'return': do_return,
        'end': do_end,
        'verify': do_verify
    }
    # print(ip, op, left, right, res)
    if op != 'goto' and op != 'gosub' and op != 'verify' and op != 'end' and op != 'end_func' and op != 'era':
        left = check_if_address(left)
        right = check_if_address(right)
        res = check_if_address(res)
    try:
        operations[op](left, right, res)
    except Exception as e:
        print(e)
        exit(1)
    if op != 'goto' and op != 'goto_f' and op != 'gosub':
        ip += 1


if __name__ == '__main__':
    filename = sys.argv[1]

    with open(filename) as infile:
        foo = infile.readline().split(' ')[2].split('\u001f')
        ints, floats, strings, bools, _voids, *_ = foo
        global_mem = Memory(ints, floats, strings, bools)
        while True:
            readline = infile.readline()
            if readline == '#\n':
                break
            reconstruct_func_dir(readline)
        ints, floats, strings, bools, * \
            _ = func_dir['main']['num_types'].split('\u001f')
        local_mems.append(Memory(ints, floats, strings, bools))
        ints, floats, strings, bools, * \
            _ = func_dir['main']['num_temps'].split('\u001f')
        temp_mems.append(Memory(ints, floats, strings, bools))
        while True:
            readline = infile.readline()
            if readline == '#\n':
                break
            class_name, num_types, *_ = readline.rstrip('\n').split(' ')
            class_dir[class_name] = {'num_types': num_types}
            while True:
                readline = infile.readline()
                if readline == '%\n':
                    break
                reconstruct_class_dir(readline, class_name)
        constants_mem = initialize_constant_mem(infile)
        quads = infile.readlines()
        while ip < len(quads):
            op, left, right, res = quads[ip].rstrip('\n').split(' ')
            run_quad(op, left, right, res)
