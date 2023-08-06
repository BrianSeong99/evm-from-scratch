#!/usr/bin/env python3

# EVM From Scratch
# Python template
#
# To work on EVM From Scratch in Python:
#
# - Install Python3: https://www.python.org/downloads/
# - Go to the `python` directory: `cd python`
# - Edit `evm.py` (this file!), see TODO below
# - Run `python3 evm.py` to run the tests

import json
import os
import math

def evm(code):
    pc = 0
    success = True
    stack = []
    MAX_UINT256 = (2**256)

    def get_n_of_stack_elements(n, stack):
        if n == 1:
            return stack.pop(0)
        elif n == 2:
            return stack.pop(0), stack.pop(0)
        elif n == 3:
            return stack.pop(0), stack.pop(0), stack.pop(0)
        
    def is_num_negative(num):
        if num == 0:
            return False, None
        elif num.bit_length() % 8 == 0:
            return True, int(num.bit_length() / 8)
        return False, None

    def negative_to_positive(num, byte_size):
        return ((0x1 << byte_size * 8) - num)

    while pc < len(code):
        op = code[pc]
        pc += 1

        # TODO: implement the EVM here!
        if op == 0x00:
            # STOP
            break

        elif op == 0x01:
            # ADD (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 + num2
            value = value if value <= MAX_UINT256 else value - MAX_UINT256
            stack.insert(0, value)
        
        elif op == 0x02:
            # MUL (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 * num2
            value = value if value <= MAX_UINT256 else value - MAX_UINT256
            stack.insert(0, value)

        elif op == 0x03:
            # SUB (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 - num2
            value = value if value >= 0 else MAX_UINT256 + value
            stack.insert(0, value)

        elif op == 0x04:
            # DIV (whole) (by zero)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = 0 if num2 == 0 else math.floor(num1 / num2)
            stack.insert(0, value)
        
        elif op == 0x05:
            # SDIV (negative) (mix of negative and positive) (by zero)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num2 == 0:
                stack.insert(0, 0)
                continue
            num1_is_negative, num1_byte_size = is_num_negative(num1)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if not num1_is_negative and not num2_is_negative:
                # both positive
                value = num1 / num2
                stack.insert(0, value)
            elif num1_is_negative and num2_is_negative:
                # both negative
                value = math.floor(negative_to_positive(num1, num1_byte_size) / negative_to_positive(num2, num2_byte_size))
                stack.insert(0, value)
            elif num1_is_negative:
                # only one negative, and num1 is negative
                value = math.floor(negative_to_positive(num1, num1_byte_size) / num2)
                padding = 1
                counter = 0
                while counter < num1.bit_length():
                    padding = padding << 1
                    counter += 1
                stack.insert(0, padding - value)
            elif num2_is_negative:
                # only one negative, and num2 is negative
                value = math.floor(num1 / negative_to_positive(num2, num2_byte_size))
                padding = 1
                counter = 0
                while counter < num2.bit_length():
                    padding = padding << 1
                    counter += 1
                stack.insert(0, padding - value)

        elif op == 0x06:
            # MOD (by larger number) (by zero)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 if num1 < num2 \
                else 0 if num2 == 0 \
                else num1 % num2
            stack.insert(0, value)

        elif op == 0x07:
            # SMOD (negative) (by zero)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num2 == 0:
                stack.insert(0, 0)
                continue
            num1_is_negative, num1_byte_size = is_num_negative(num1)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num2_is_negative:
                num2 = negative_to_positive(num2, num2_byte_size)
            if num1_is_negative:
                num1 = negative_to_positive(num1, num1_byte_size)
                value = negative_to_positive((num1 % num2), num1_byte_size)
                stack.insert(0, value)
            else:
                value = num1 % num2
                stack.insert(0, value)

        elif op == 0x08:
            # ADDMOD (wrapped)
            num1, num2, num3 = get_n_of_stack_elements(3, stack)
            value = (num1 + num2) % num3
            stack.insert(0, value)
        
        elif op == 0x09:
            # MULMOD (wrapped)
            num1, num2, num3 = get_n_of_stack_elements(3, stack)
            value = (num1 * num2) % num3
            stack.insert(0, value)

        elif op == 0x0a:
            # EXP
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 ** num2
            stack.insert(0, value)
        
        elif op == 0x0b:
            # SIGNEXTEND (positive)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num2_bit_length = num2.bit_length()
            if num2_bit_length % 8 != 0:
                stack.insert(0, num2)
            else:
                padding = 1
                counter = 0
                while counter < num2_bit_length:
                    padding = padding << 1
                    counter += 1
                stack.insert(0, MAX_UINT256 - padding + num2)
        
        elif op == 0x10:
            # LT (equal) (greater)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num1 - num2 < 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x11:
            # GT (equal) (less)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num1 - num2 > 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x12:
            # SLT (equal) (less)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num1_is_negative, num1_byte_size = is_num_negative(num1)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num1_is_negative and num2_is_negative:
                num1 = negative_to_positive(num1, num1_byte_size)
                num2 = negative_to_positive(num2, num2_byte_size)
                stack.insert(0, 1 if num1 - num2 > 0 else 0)
            elif num1_is_negative:
                stack.insert(0, 1)
            elif num2_is_negative:
                stack.insert(0, 0)
            else:
                stack.insert(0, 1 if num1 - num2 < 0 else 0)
        
        elif op == 0x13:
            # SGT (equal) (greater)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num1_is_negative, num1_byte_size = is_num_negative(num1)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num1_is_negative and num2_is_negative:
                num1 = negative_to_positive(num1, num1_byte_size)
                num2 = negative_to_positive(num2, num2_byte_size)
                stack.insert(0, 1 if num1 - num2 < 0 else 0)
            elif num2_is_negative:
                stack.insert(0, 1)
            elif num1_is_negative:
                stack.insert(0, 0)
            else:
                stack.insert(0, 1 if num1 - num2 > 0 else 0)
        
        elif op == 0x14:
            # EQ (not equal)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num1 - num2 == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)

        elif op == 0x15:
            # ISZERO (not zero) (zero)
            num1 = get_n_of_stack_elements(1, stack)
            if num1 == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x16:
            # AND
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 & num2
            stack.insert(0, value)
        
        elif op == 0x17:
            # AND
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 | num2
            stack.insert(0, value)
        
        elif op == 0x18:
            # AND
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = num1 ^ num2
            stack.insert(0, value)

        elif op == 0x19:
            # NOT
            num1 = get_n_of_stack_elements(1, stack)
            value = MAX_UINT256-1 - num1
            stack.insert(0, value)

        elif op == 0x5f:
            # PUSH0
            stack.insert(0, 0)
            
        elif op >= 0x60 and op <= 0x7f:
            # PUSH1 - PUSH32
            size = op - 0x60
            value = 0
            while size >= 0:
                value = value | code[pc] << size * 8
                pc += 1
                size -= 1
            stack.insert(0, value)
        
        elif op == 0x50:
            # POP
            get_n_of_stack_elements(1, stack)
            success = True

    return (success, stack)

def test():
    script_dirname = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dirname, "..", "evm.json")
    with open(json_file) as f:
        data = json.load(f)
        total = len(data)

        for i, test in enumerate(data):
            # Note: as the test cases get more complex, you'll need to modify this
            # to pass down more arguments to the evm function
            code = bytes.fromhex(test['code']['bin'])
            (success, stack) = evm(code)

            expected_stack = [int(x, 16) for x in test['expect']['stack']]
            
            if stack != expected_stack or success != test['expect']['success']:
                print(f"❌ Test #{i + 1}/{total} {test['name']}")
                if stack != expected_stack:
                    print("Stack doesn't match")
                    print(" expected:", expected_stack)
                    print("   actual:", stack)
                else:
                    print("Success doesn't match")
                    print(" expected:", test['expect']['success'])
                    print("   actual:", success)
                print("")
                print("Test code:")
                print(test['code']['asm'])
                print("")
                print("Hint:", test['hint'])
                print("")
                print(f"Progress: {i}/{len(data)}")
                print("")
                break
            else:
                print(f"✓  Test #{i + 1}/{total} {test['name']}")

if __name__ == '__main__':
    test()
