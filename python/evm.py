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
        elif n == 4:
            return stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0)
        
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

    def padding_address(address):
        return '0x' + '0'*(22 - len(address)) + address[2:] if len(address) < 22 else address

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
            a, b = get_n_of_stack_elements(2, stack)
            value = (a + b)  % (MAX_UINT256+1)
            stack.insert(0, value)
        
        elif op == 0x02:
            # MUL (overflow)
            a, b = get_n_of_stack_elements(2, stack)
            value = (a * b)  % (MAX_UINT256+1)
            stack.insert(0, value)

        elif op == 0x03:
            # SUB (overflow)
            a, b = get_n_of_stack_elements(2, stack)
            value = (a - b)  % (MAX_UINT256+1)
            stack.insert(0, value)

        elif op == 0x04:
            # DIV (whole) (by zero)
            a, b = get_n_of_stack_elements(2, stack)
            value = 0 if b == 0 else math.floor(a / b)
            stack.insert(0, value)
        
        elif op == 0x05:
            # SDIV (negative) (mix of negative and positive) (by zero)
            print("SDIV", stack)
            a, b = get_n_of_stack_elements(2, stack)
            if b == 0:
                stack.insert(0, 0)
            else:
                a_is_negative, a_byte_size = is_num_negative(a)
                b_is_negative, b_byte_size = is_num_negative(b)
                if not a_is_negative and not b_is_negative:
                    # both positive
                    value = a / b
                    stack.insert(0, value)
                elif a_is_negative and b_is_negative:
                    # both negative
                    value = math.floor(negative_to_positive(a, a_byte_size) / negative_to_positive(b, b_byte_size))
                    stack.insert(0, value)
                elif a_is_negative:
                    # only one negative, and a is negative
                    value = math.floor(negative_to_positive(a, a_byte_size) / b)
                    padding = 1
                    counter = 0
                    while counter < a.bit_length():
                        padding = padding << 1
                        counter += 1
                    stack.insert(0, padding - value)
                elif b_is_negative:
                    # only one negative, and b is negative
                    value = math.floor(a / negative_to_positive(b, b_byte_size))
                    padding = 1
                    counter = 0
                    while counter < b.bit_length():
                        padding = padding << 1
                        counter += 1
                    stack.insert(0, padding - value)

        elif op == 0x06:
            # MOD (by larger number) (by zero)
            a, b = get_n_of_stack_elements(2, stack)
            value = a if a < b \
                else 0 if b == 0 \
                else a % b
            stack.insert(0, value)

        elif op == 0x07:
            # SMOD (negative) (by zero)
            a, b = get_n_of_stack_elements(2, stack)
            if b == 0:
                stack.insert(0, 0)
            else:
                a_is_negative, a_byte_size = is_num_negative(a)
                b_is_negative, b_byte_size = is_num_negative(b)
                if b_is_negative:
                    b = negative_to_positive(b, b_byte_size)
                if a_is_negative:
                    a = negative_to_positive(a, a_byte_size)
                    value = negative_to_positive((a % b), a_byte_size)
                    stack.insert(0, value)
                else:
                    value = a % b
                    stack.insert(0, value)

        elif op == 0x08:
            # ADDMOD (wrapped)
            a, b, N = get_n_of_stack_elements(3, stack)
            value = (a + b) % N
            stack.insert(0, value)
        
        elif op == 0x09:
            # MULMOD (wrapped)
            a, b, N = get_n_of_stack_elements(3, stack)
            value = (a * b) % N
            stack.insert(0, value)

        elif op == 0x0a:
            # EXP
            a, exponent = get_n_of_stack_elements(2, stack)
            value = a ** exponent
            stack.insert(0, value)
        
        elif op == 0x0b:
            # SIGNEXTEND (positive)
            b, x = get_n_of_stack_elements(2, stack)
            x_bit_length = x.bit_length()
            if x_bit_length % BYTE_SIZE != 0:
                stack.insert(0, x)
            else:
                padding = 1
                counter = 0
                while counter < x_bit_length:
                    padding = padding << 1
                    counter += 1
                padding = padding - 1 # after bit shift, need to minus one
                stack.insert(0, MAX_UINT256 - padding + x)
        
        elif op == 0x10:
            # LT (equal) (greater)
            a, b = get_n_of_stack_elements(2, stack)
            if a - b < 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x11:
            # GT (equal) (less)
            a, b = get_n_of_stack_elements(2, stack)
            if a - b > 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x12:
            # SLT (equal) (less)
            a, b = get_n_of_stack_elements(2, stack)
            a_is_negative, a_byte_size = is_num_negative(a)
            b_is_negative, b_byte_size = is_num_negative(b)
            if a_is_negative and b_is_negative:
                a = negative_to_positive(a, a_byte_size)
                b = negative_to_positive(b, b_byte_size)
                stack.insert(0, 1 if a - b > 0 else 0)
            elif a_is_negative:
                stack.insert(0, 1)
            elif b_is_negative:
                stack.insert(0, 0)
            else:
                stack.insert(0, 1 if a - b < 0 else 0)
        
        elif op == 0x13:
            # SGT (equal) (greater)
            a, b = get_n_of_stack_elements(2, stack)
            a_is_negative, a_byte_size = is_num_negative(a)
            b_is_negative, b_byte_size = is_num_negative(b)
            if a_is_negative and b_is_negative:
                a = negative_to_positive(a, a_byte_size)
                b = negative_to_positive(b, b_byte_size)
                stack.insert(0, 1 if a - b < 0 else 0)
            elif b_is_negative:
                stack.insert(0, 1)
            elif a_is_negative:
                stack.insert(0, 0)
            else:
                stack.insert(0, 1 if a - b > 0 else 0)
        
        elif op == 0x14:
            # EQ (not equal)
            a, b = get_n_of_stack_elements(2, stack)
            if a - b == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)

        elif op == 0x15:
            # ISZERO (not zero) (zero)
            a = get_n_of_stack_elements(1, stack)
            if a == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        elif op == 0x16:
            # AND
            a, b = get_n_of_stack_elements(2, stack)
            value = a & b
            stack.insert(0, value)
        
        elif op == 0x17:
            # OR
            a, b = get_n_of_stack_elements(2, stack)
            value = a | b
            stack.insert(0, value)
        
        elif op == 0x18:
            # XOR
            a, b = get_n_of_stack_elements(2, stack)
            value = a ^ b
            stack.insert(0, value)

        elif op == 0x19:
            # NOT
            a = get_n_of_stack_elements(1, stack)
            value = MAX_UINT256 - a
            stack.insert(0, value)
        
        elif op == 0x1a:
            # BYTE
            byte_offset, num = get_n_of_stack_elements(2, stack)
            if byte_offset > 31 or byte_offset < 0: # (out of range)
                stack.insert(0, 0)
            else:
                high_bit_mask = (0x1 << ((32 - byte_offset) * 8)) - 1
                low_bit_mask = (0x1 << ((32 - byte_offset - 1) * 8)) - 1 if 32 - byte_offset - 1 > 0 else 0
                bit_mask = high_bit_mask ^ low_bit_mask
                value = (num & bit_mask) >> (32 - byte_offset - 1) * 8
                stack.insert(0, value)

        elif op == 0x1b:
            # SHL (discards) (too large)
            shift, num = get_n_of_stack_elements(2, stack)
            num_is_negative, num_byte_size = is_num_negative(num)
            if shift >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards)
                value = extract_lower_bits(num, num_byte_size * BYTE_SIZE - shift) << shift
                stack.insert(0, value)

        elif op == 0x1c:
            # SHR (discards) (too large)
            shift, num = get_n_of_stack_elements(2, stack)
            num_is_negative, num_byte_size = is_num_negative(num)
            if shift >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards) 
                value = num >> shift
                stack.insert(0, value)

        elif op == 0x1d:
            # SAR (fills 1s) (too large) (positive, too large)
            shift, num = get_n_of_stack_elements(2, stack)
            num_is_negative, num_byte_size = is_num_negative(num)
            if shift >= MAX_UINT32:  # (too large) 
                if num_is_negative:
                    stack.insert(0, (0x1 << (num_byte_size * BYTE_SIZE)) - 1)
                else:
                    stack.insert(0, 0)
            else:
                if num_is_negative: # (fills 1s) 
                    bit_mask = ((0x1 << num_byte_size * BYTE_SIZE) - 1) ^ ((0x1 << (num_byte_size * BYTE_SIZE - shift)) - 1)
                    value = (num >> shift) | bit_mask
                    stack.insert(0, value)
                else: # positive
                    value = num >> shift
                    stack.insert(0, value)

        elif op == 0x20:
            # SHA3
            byte_offset, byte_size = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + byte_size:
                memory += ([0] * (byte_offset + 32 - len(memory)))
            value = 0
            for i in range(byte_size):
                value = value << BYTE_SIZE
                value += memory[byte_offset + i]
            hashed_value = int.from_bytes(keccak(value.to_bytes(byte_size, byteorder='big')), byteorder="big")
            stack.insert(0, hashed_value)

        elif op == 0x30:
            # ADDRESS
            address = int(tx['to'], 16)
            stack.insert(0, address)

        elif op == 0x31:
            # BALANCE
            address = get_n_of_stack_elements(1, stack)
            if state is not None and hex(address) in state:
                balance = int(state[hex(address)]["balance"], 16)
                stack.insert(0, balance)
            else:
                stack.insert(0, 0)
        
        elif op == 0x32:
            # ORIGIN
            address = int(tx['origin'], 16)
            stack.insert(0, address)

        elif op == 0x33:
            # CALLER
            address = int(tx['from'], 16)
            stack.insert(0, address)
        
        elif op == 0x34:
            # CALLVALUE
            value = int(tx['value'], 16)
            stack.insert(0, value)
        
        elif op == 0x35:
            # CALLDATALOAD
            byte_offset = get_n_of_stack_elements(1, stack)
            data = int(tx['data'], 16)
            data = (data << (BYTE_SIZE * byte_offset)) & ((0x1 << 256) - 1) # (tail)
            stack.insert(0, data)

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
            data = int(tx['data'], 16)
            bit_mask = ((0x1 << 256) - 1) ^ ((0x1 << (256 - byte_size * 8)) - 1)
            data = (data << (BYTE_SIZE * byte_offset)) & bit_mask # (tail)
            if len(memory) < dest_offset + 32: # (tail)
                memory += [0] * (dest_offset + 32 - len(memory))
            for i in range(32):
                memory[dest_offset + 31 - i] = (data >> (i * 8)) & 0xFF

        elif op == 0x38:
            # CODESIZE (small)
            stack.insert(0, len(code))
        
        elif op == 0x39:
            # CODECOPY
            dest_offset, byte_offset, byte_size = get_n_of_stack_elements(3, stack)
            if len(memory) < dest_offset + byte_size:
                memory += ([0] * (dest_offset + byte_size - len (memory)))
            data = code
            for i in range(byte_size):
                if (byte_offset + i) < len(data):
                    memory[dest_offset + i] = data[byte_offset + i]
                else:
                    memory[dest_offset + i] = 0

        elif op == 0x3a:
            # Gasprice
            gasprice = int(tx['gasprice'], 16)
            stack.insert(0, gasprice)
        
        elif op == 0x3b:
            # EXTCODESIZE
            address = hex(get_n_of_stack_elements(1, stack))
            address = padding_address(address)
            if state is None or address not in state or 'code' not in state[address]:
                stack.insert(0, 0)
            else:
                stack.insert(0, len(state[address]['code']['bin']) / 2)
        
        elif op == 0x3c:
            # EXTCODECOPY
            address, dest_offset, byte_offset, byte_size = get_n_of_stack_elements(4, stack)
            address = padding_address(hex(address))
            
            extcode = b''
            if state is None or address not in state or 'code' not in state[address]:
                extcode = b''
            else:
                extcode = bytes.fromhex(state[address]['code']['bin'])
            
            if len(memory) < dest_offset + byte_size:
                memory += ([0] * (dest_offset + byte_size - len (memory)))
            for i in range(byte_size):
                if (byte_offset + i) < len(extcode):
                    memory[dest_offset + i] = extcode[byte_offset + i]
                else:
                    memory[dest_offset + i] = 0

        elif op == 0x3f:
            # EXTCODEHASH
            address = hex(get_n_of_stack_elements(1, stack))
            address = padding_address(address)
            if state is None or address not in state or 'code' not in state[address]:
                stack.insert(0, 0)
            else:
                extcode = bytes.fromhex(state[address]['code']['bin'])
                stack.insert(0, int.from_bytes(keccak(extcode), byteorder='big'))

        elif op == 0x40:
            # BLOCKHASH
            pass

        elif op == 0x41:
            # COINBASE
            coinbase = int(block['coinbase'], 16)
            stack.insert(0, coinbase)
        
        elif op == 0x42:
            # TIMESTAMP
            timestamp = int(block['timestamp'], 16)
            stack.insert(0, timestamp)
        
        elif op == 0x43:
            # BLOCKNUMBER
            blocknumber = int(block['number'], 16)
            stack.insert(0, blocknumber)

        elif op == 0x44:
            # DIFFICULTY
            difficulty = int(block['difficulty'], 16)
            stack.insert(0, difficulty)

        elif op == 0x45:
            # GASLIMIT
            gaslimit = int(block['gaslimit'], 16)
            stack.insert(0, gaslimit)
        
        elif op == 0x46:
            # CHAINID
            chainid = int(block['chainid'], 16)
            stack.insert(0, chainid)
        
        elif op == 0x47:
            # SELFBALANCE
            address = tx["to"]
            if state is None or address not in state or 'balance' not in state[address]:
                stack.insert(0, 0)
            else:
                stack.insert(0, int(state[address]['balance'], 16))

        elif op == 0x48:
            # BASEFEE
            basefee = int(block['basefee'], 16)
            stack.insert(0, basefee)

        elif op == 0x50:
            # POP
            get_n_of_stack_elements(1, stack)
            success = True
        
        elif op == 0x51:
            # MLOAD
            byte_offset = get_n_of_stack_elements(1, stack)
            if len(memory) < byte_offset + 32:
                memory += ([0] * (byte_offset + 32 - len(memory)))
            data = 0
            for i in range(32):
                data = data << BYTE_SIZE
                data += memory[byte_offset + i]
            stack.insert(0, data)

        elif op == 0x52:
            # MSTORE
            byte_offset, num = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + 32: # (tail)
                memory += [0] * (byte_offset + 32 - len(memory))
            for i in range(32):
                memory[byte_offset + 31 - i] = (num >> (i * 8)) & 0xFF

        elif op == 0x53:
            # MSTORE8
            byte_offset, num = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + 1:
                memory += [0] * (byte_offset + 1 - len(memory))
            memory[byte_offset] = num & 0xff

        elif op == 0x56:
            # JUMP
            counter = get_n_of_stack_elements(1, stack)
            if code[counter] == 0x5b and not is_invalid_JUMPDEST(counter):
                pc = counter
                continue
            else:
                success = False
                break
        
        elif op == 0x57:
            # JUMPI
            counter, b = get_n_of_stack_elements(2, stack)
            if b == 0:
                pass
            else:
                if code[counter] == 0x5b and not is_invalid_JUMPDEST(counter):
                    pc = counter
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
