import copy


class Directory():
    directory = {}
    types = ['int', 'float', 'string', 'bool', 'void']

    def __get_num_type(self, scope, idx):
        num_types = self.directory[scope]['num_types'].split('\u001f')
        return int(num_types[idx])

    def __get_num_temp(self, scope, idx):
        num_temps = self.directory[scope]['num_temps'].split('\u001f')
        return int(num_temps[idx])

    def __update_num_types(self, scope, idx, quantity=1):
        num_types = self.directory[scope]['num_types'].split('\u001f')
        num_types[idx] = str(int(num_types[idx]) + quantity)
        self.directory[scope]['num_types'] = '\u001f'.join(num_types)

    def __update_num_temps(self, scope, idx):
        num_temps = self.directory[scope]['num_temps'].split('\u001f')
        num_temps[idx] = str(int(num_temps[idx]))
        self.directory[scope]['num_temps'] = '\u001f'.join(num_temps)

    def add_array(self, id, scope, size):
        self.directory[scope]['vars'][id] = {
            'd1': size
        }

    def add_function_var(self, id, scope, type):
        idx = self.types.index(type)
        address = idx * 300 + self.__get_num_type(scope, idx)
        self.directory[scope]['vars'][id] = {
            'type': type,
            'dir': -1,
            'real_dir': address
        }
        self.__update_num_types(scope, idx)

    def add_function_parameter(self, id, scope, type):
        idx = self.types.index(type)
        self.directory[scope]['params'] += str(idx)

        address = 1500 + idx * 300 + self.__get_num_type(scope, idx)
        self.directory[scope]['vars'][id] = {
            'type': type,
            'dir': address
        }
        self.__update_num_types(scope, idx)

    def add_object(self, id, scope, type):
        self.directory[scope]['vars'][id] = {
            'type': type
        }

    def add_scope(self, id, return_type=None, is_global=False):
        self.directory[id] = {
            'return_type': return_type,
            'vars': {},
            'num_types': '0\u001f' * 5,
        }

        if not is_global:
            self.directory[id]['num_temps'] = '0\u001f' * 4
            self.directory[id]['params'] = '0\u001f' * 4

    def add_temp(self, scope, type, counter):
        idx = self.types.index(type)
        t_num = self.__get_num_temp(scope, idx)
        address = idx * 300 + t_num + 3000
        self.__update_num_temps(scope, idx)
        return {
            'value': 't' + str(counter),
            'type': type,
            'dir': address
        }

    def add_variable(self, id, scope, type, offset=0):
        idx = self.types.index(type)
        address = idx * 300 + self.__get_num_type(scope, idx) + offset
        self.directory[scope]['vars'][id] = {
            'type': type,
            'dir': -1,
            'real_dir': address
        }
        self.__update_num_types(scope, idx)

    def delete_var_table(self, scope):
        del self.directory[scope]['vars']

    def get_directory(self):
        return self.directory

    def get_function_address(self, id, scope):
        return self.directory[scope]['vars'][id]['real_dir']

    def get_function_params(self, id):
        return self.directory[id]['params']

    def get_var_address(self, id, scope):
        return self.directory[scope]['vars'][id]['dir']

    def get_var_d1(self, id, scope):
        return self.directory[scope]['vars'][id]['d1']

    def get_var_d2(self, id, scope):
        return self.directory[scope]['vars'][id]['d2']

    def get_var_type(self, id, scope):
        return self.directory[scope]['vars'][id]['type']

    def has_id(self, id, scope=None):
        if scope:
            return id in self.directory or id in self.directory[scope]['vars']
        return id in self.directory

    def inherit_content(self, id, inherited):
        self.directory[id] = copy.deepcopy(self.directory[inherited])

    def scope_has_id(self, id, scope):
        return id in self.directory[scope]['vars']

    def set_array_address(self, id, scope, base=0):
        type = self.get_var_type(id, scope)
        idx = self.types.index(type)
        address = idx * 300 + self.__get_num_type(scope, idx) + base
        quantity = self.directory[scope]['vars'][id]['d1']
        if 'd2' in self.directory[scope]['vars'][id]:
            quantity *= self.directory[scope]['vars'][id]['d2']
        self.directory[scope]['vars'][id]['dir'] = address
        self.__update_num_types(scope, idx, quantity)

    def set_function_start(self, function, start):
        self.directory[function]['start'] = start

    def set_matrix_d2(self, id, scope, size):
        self.directory[scope]['vars'][id]['d2'] = size

    def set_var_address(self, id, scope, base=0):
        type = self.get_var_type(id, scope)
        idx = self.types.index(type)
        address = idx * 300 + self.__get_num_type(scope, idx) + base
        self.directory[scope]['vars'][id]['dir'] = address
        self.__update_num_types(scope, idx)

    def set_var_type(self, id, scope, type):
        self.directory[scope]['vars'][id]['type'] = type

    def update_var_address(self, id, scope, address):
        self.directory[scope]['vars'][id]['dir'] = address

    def var_is_array(self, id, scope):
        return 'd1' in self.directory[scope]['vars'][id]

    def var_is_matrix(self, id, scope):
        return 'd2' in self.directory[scope]['vars'][id]
