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
from eth_hash.auto import keccak

def evm(code, tx, block, state):
    pc = 0
    success = True
    stack = []
    memory = []
    BYTE_SIZE = 8
    MAX_UINT256 = 2**256 - 1
    MAX_UINT32 = 2**32 - 1

    def get_n_of_stack_elements(n, stack):
        if n == 1:
            return stack.pop(0)
        elif n == 2:
            return stack.pop(0), stack.pop(0)
        elif n == 3:
            return stack.pop(0), stack.pop(0), stack.pop(0)
        
    def is_num_negative(num):
        if num == 0:
            return False, None # The Byte Size here should be dependent to the num format
        if num.bit_length() % BYTE_SIZE == 0:
            return True, int(num.bit_length() / BYTE_SIZE)
        return False, int(math.floor(num.bit_length() / BYTE_SIZE))+1

    def negative_to_positive(num, byte_size):
        return ((0x1 << byte_size * BYTE_SIZE) - num)

    def extract_lower_bits(num, n_bits):
        bit_mask = (0x1 << n_bits) - 1
        return num & bit_mask

    def is_invalid_JUMPDEST(destination_offset):
        for i in range(1, 33):
            index = destination_offset - i
            if index >= 0 and code[index] >= 0x5f + i and code[index] < 0x80:
                return True
        return False

    while pc < len(code):
        op = code[pc]
        # print()
        # print("opcode: ", hex(op))

        # TODO: implement the EVM here!
        if op == 0x00:
            # STOP
            break

        elif op == 0x01:
            # ADD (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = (num1 + num2)  % (MAX_UINT256+1)
            stack.insert(0, value)
        
        elif op == 0x02:
            # MUL (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = (num1 * num2)  % (MAX_UINT256+1)
            stack.insert(0, value)

        elif op == 0x03:
            # SUB (overflow)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = (num1 - num2)  % (MAX_UINT256+1)
            stack.insert(0, value)

        elif op == 0x04:
            # DIV (whole) (by zero)
            num1, num2 = get_n_of_stack_elements(2, stack)
            value = 0 if num2 == 0 else math.floor(num1 / num2)
            stack.insert(0, value)
        
        elif op == 0x05:
            # SDIV (negative) (mix of negative and positive) (by zero)
            print("SDIV", stack)
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num2 == 0:
                stack.insert(0, 0)
            else:
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
            else:
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
            if num2_bit_length % BYTE_SIZE != 0:
                stack.insert(0, num2)
            else:
                padding = 1
                counter = 0
                while counter < num2_bit_length:
                    padding = padding << 1
                    counter += 1
                padding = padding - 1 # after bit shift, need to minus one
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
            value = MAX_UINT256 - num1
            stack.insert(0, value)
        
        elif op == 0x1a:
            # BYTE
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num1 > 31 or num1 < 0: # (out of range)
                stack.insert(0, 0)
            else:
                high_bit_mask = (0x1 << ((32 - num1) * 8)) - 1
                low_bit_mask = (0x1 << ((32 - num1 - 1) * 8)) - 1 if 32 - num1 - 1 > 0 else 0
                bit_mask = high_bit_mask ^ low_bit_mask
                value = (num2 & bit_mask) >> (32 - num1 - 1) * 8
                stack.insert(0, value)

        elif op == 0x1b:
            # SHL (discards) (too large)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num1 >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards)
                value = extract_lower_bits(num2, num2_byte_size * BYTE_SIZE - num1) << num1
                stack.insert(0, value)

        elif op == 0x1c:
            # SHR (discards) (too large)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num1 >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards) 
                value = num2 >> num1
                stack.insert(0, value)

        elif op == 0x1d:
            # SAR (fills 1s) (too large) (positive, too large)
            num1, num2 = get_n_of_stack_elements(2, stack)
            num2_is_negative, num2_byte_size = is_num_negative(num2)
            if num1 >= MAX_UINT32:  # (too large) 
                if num2_is_negative:
                    stack.insert(0, (0x1 << (num2_byte_size * BYTE_SIZE)) - 1)
                else:
                    stack.insert(0, 0)
            else:
                if num2_is_negative: # (fills 1s) 
                    bit_mask = ((0x1 << num2_byte_size * BYTE_SIZE) - 1) ^ ((0x1 << (num2_byte_size * BYTE_SIZE - num1)) - 1)
                    value = (num2 >> num1) | bit_mask
                    stack.insert(0, value)
                else: # positive
                    value = num2 >> num1
                    stack.insert(0, value)

        elif op == 0x20:
            # SHA3
            num1, num2 = get_n_of_stack_elements(2, stack)
            if len(memory) < num1 + num2:
                memory += ([0] * (num1 + 32 - len(memory)))
            value = 0
            for i in range(num2):
                value = value << BYTE_SIZE
                value += memory[num1 + i]
            hashed_value = int.from_bytes(keccak(value.to_bytes(num2, byteorder='big')), byteorder="big")
            stack.insert(0, hashed_value)

        elif op == 0x30:
            # Address
            value = int(tx['to'], 16)
            stack.insert(0, value)

        elif op == 0x31:
            # Balance
            num1 = get_n_of_stack_elements(1, stack)
            if state is not None and hex(num1) in state:
                value = int(state[hex(num1)]["balance"], 16)
                stack.insert(0, value)
            else:
                stack.insert(0, 0)
        
        elif op == 0x32:
            # Origin
            value = int(tx['origin'], 16)
            stack.insert(0, value)

        elif op == 0x33:
            # Caller
            value = int(tx['from'], 16)
            stack.insert(0, value)
        
        elif op == 0x34:
            # CALLVALUE
            value = int(tx['value'], 16)
            stack.insert(0, value)
        
        elif op == 0x35:
            # CALLDATALOAD
            byte_offset = get_n_of_stack_elements(1, stack)
            value = int(tx['data'], 16)
            value = (value << (BYTE_SIZE * byte_offset)) & ((0x1 << 256) - 1) # (tail)
            stack.insert(0, value)

        elif op == 0x36:
            # CALLDATASIZE
            if tx is not None:
                data = int(tx.get('data', 0), 16)
                count = 1
                while data > 0:
                    data = data >> BYTE_SIZE
                    count += 1
                stack.insert(0, count)
            else:
                stack.insert(0, 0)

        elif op == 0x37:
            # CALLDATACOPY
            dest_offset, byte_offset, byte_size = get_n_of_stack_elements(3, stack)
            value = int(tx['data'], 16)
            bit_mask = ((0x1 << 256) - 1) ^ ((0x1 << (256 - byte_size * 8)) - 1)
            value = (value << (BYTE_SIZE * byte_offset)) & bit_mask # (tail)
            if len(memory) < dest_offset + 32: # (tail)
                memory += [0] * (dest_offset + 32 - len(memory))
            for i in range(32):
                memory[dest_offset + 31 - i] = (value >> (i * 8)) & 0xFF

        elif op == 0x3a:
            # Gasprice
            value = int(tx['gasprice'], 16)
            stack.insert(0, value)
        
        elif op == 0x40:
            # Blockhash
            pass

        elif op == 0x41:
            # Coinbase
            value = int(block['coinbase'], 16)
            stack.insert(0, value)
        
        elif op == 0x42:
            # Timestamp
            value = int(block['timestamp'], 16)
            stack.insert(0, value)
        
        elif op == 0x43:
            # Block Number
            value = int(block['number'], 16)
            stack.insert(0, value)

        elif op == 0x44:
            # Difficulty
            value = int(block['difficulty'], 16)
            stack.insert(0, value)

        elif op == 0x45:
            # GasLimit
            value = int(block['gaslimit'], 16)
            stack.insert(0, value)
        
        elif op == 0x46:
            # Chainid
            value = int(block['chainid'], 16)
            stack.insert(0, value)

        elif op == 0x48:
            # Basefee
            value = int(block['basefee'], 16)
            stack.insert(0, value)

        elif op == 0x50:
            # POP
            get_n_of_stack_elements(1, stack)
            success = True
        
        elif op == 0x51:
            # MLOAD
            num1 = get_n_of_stack_elements(1, stack)
            if len(memory) < num1 + 32:
                memory += ([0] * (num1 + 32 - len(memory)))
            value = 0
            for i in range(32):
                value = value << BYTE_SIZE
                value += memory[num1 + i]
            stack.insert(0, value)

        elif op == 0x52:
            # MSTORE
            byte_offset, num = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + 32: # (tail)
                memory += [0] * (byte_offset + 32 - len(memory))
            for i in range(32):
                memory[byte_offset + 31 - i] = (num >> (i * 8)) & 0xFF

        elif op == 0x53:
            # MSTORE8
            num1, num2 = get_n_of_stack_elements(2, stack)
            if len(memory) < num1 + 1:
                memory += [0] * (num1 + 1 - len(memory))
            memory[num1] = num2 & 0xff

        elif op == 0x56:
            # JUMP
            num = get_n_of_stack_elements(1, stack)
            if code[num] == 0x5b and not is_invalid_JUMPDEST(num):
                pc = num
                continue
            else:
                success = False
                break
        
        elif op == 0x57:
            # JUMPI
            num1, num2 = get_n_of_stack_elements(2, stack)
            if num2 == 0:
                pass
            else:
                if code[num1] == 0x5b and not is_invalid_JUMPDEST(num1):
                    pc = num1
                    continue
                else:
                    success = False
                    break
        
        elif op == 0x58:
            # PC
            stack.insert(0, pc)

        elif op == 0x59:
            # MSIZE
            value = math.ceil(len(memory) / 32) * 32
            stack.insert(0, value)

        elif op == 0x5a:
            # GAS
            stack.insert(0, MAX_UINT256)
        
        elif op == 0x5b:
            # JUMPDEST
            pass

        elif op == 0x5f:
            # PUSH0
            stack.insert(0, 0)
            
        elif op >= 0x60 and op <= 0x7f:
            # PUSH1 - PUSH32
            size = op - 0x60
            value = 0
            while size >= 0:
                pc += 1
                value = value | code[pc] << size * BYTE_SIZE
                size -= 1
            stack.insert(0, value)

        elif op >= 0x80 and op <= 0x8f:
            # DUP1 - 16
            index = op - 0x80
            num = stack[index]
            stack.insert(0, num)
        
        elif op >= 0x90 and op <= 0x9f:
            # SWAP1 - 16
            index = op - 0x90 + 1
            num = stack[index]
            stack[index] = stack[0]
            stack[0] = num
        
        elif op == 0xfe:
            # INVALID
            success = False
        
        pc += 1

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
            tx = test.get('tx')
            block = test.get('block')
            state = test.get('state')
            (success, stack) = evm(code, tx, block, state)

            expected_stack = [int(x, 16) for x in test['expect']['stack']]
            
            if stack != expected_stack or success != test['expect']['success']:
                print(f"❌ Test #{i + 1}/{total} {test['name']}")
                if stack != expected_stack:
                    print("Stack doesn't match")
                    print(" expected in decimal:", expected_stack)
                    print("   actual in decimal:", stack)
                    print(" expected in hex:", [hex(expected) for expected in expected_stack])
                    print("   actual in hex:", [hex(ele) for ele in stack])
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
