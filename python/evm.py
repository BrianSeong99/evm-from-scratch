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
    storage = {}
    logs = []
    ret = None
    last_ret = None
    BYTE_SIZE = 8
    MAX_UINT256 = 2**256 - 1
    MAX_UINT32 = 2**32 - 1

    def get_n_of_stack_elements(n, stack):
        if n <= 0:
            return None
        else:
            result = stack[:n]
            stack = stack[n:]
            return result, stack
        #     return [stack.pop(0)]
        # elif n == 2:
        #     return [stack.pop(0), stack.pop(0)]
        # elif n == 3:
        #     return [stack.pop(0), stack.pop(0), stack.pop(0)]
        # elif n == 4:
        #     return [stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0)]
        
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

    def mload(memory, byte_offset, byte_size):
        if len(memory) < byte_offset + byte_size:
            memory += ([0] * (byte_offset + byte_size - len(memory)))
        data = 0
        for i in range(byte_size):
            data = data << BYTE_SIZE
            data += memory[byte_offset + i]
        return data

    def mstore(memory, data, byte_offset, byte_size):
        if len(memory) < byte_offset + byte_size:
            memory += ([0] * (byte_offset + byte_size - len(memory)))
        for i in range(byte_size):
            memory[byte_offset + byte_size - i - 1] = (data >> (i * 8)) & 0xFF
        return memory

    while pc < len(code):
        op = code[pc]

        # STOP
        if op == 0x00:
            break

        # ADD (overflow)
        elif op == 0x01:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = (a + b)  % (MAX_UINT256+1)
            stack.insert(0, value)
        
        # MUL (overflow)
        elif op == 0x02:
            [a, b], stack  = get_n_of_stack_elements(2, stack)
            value = (a * b)  % (MAX_UINT256+1)
            stack.insert(0, value)

        # SUB (overflow)
        elif op == 0x03:
            [a, b], stack  = get_n_of_stack_elements(2, stack)
            value = (a - b)  % (MAX_UINT256+1)
            stack.insert(0, value)

        # DIV (whole) (by zero)
        elif op == 0x04:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = 0 if b == 0 else math.floor(a / b)
            stack.insert(0, value)
        
        # SDIV (negative) (mix of negative and positive) (by zero)
        elif op == 0x05:
            [a, b], stack = get_n_of_stack_elements(2, stack)
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

        # MOD (by larger number) (by zero)
        elif op == 0x06:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = a if a < b \
                else 0 if b == 0 \
                else a % b
            stack.insert(0, value)

        # SMOD (negative) (by zero)
        elif op == 0x07:
            [a, b], stack = get_n_of_stack_elements(2, stack)
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

        # ADDMOD (wrapped)
        elif op == 0x08:
            [a, b, N], stack = get_n_of_stack_elements(3, stack)
            value = (a + b) % N
            stack.insert(0, value)
        
        # MULMOD (wrapped)
        elif op == 0x09:
            [a, b, N], stack = get_n_of_stack_elements(3, stack)
            value = (a * b) % N
            stack.insert(0, value)

        # EXP
        elif op == 0x0a:
            [a, exponent], stack = get_n_of_stack_elements(2, stack)
            value = a ** exponent
            stack.insert(0, value)
        
        # SIGNEXTEND (positive)
        elif op == 0x0b:
            [b, x], stack = get_n_of_stack_elements(2, stack)
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
        
        # LT (equal) (greater)
        elif op == 0x10:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            if a - b < 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        # GT (equal) (less)
        elif op == 0x11:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            if a - b > 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        # SLT (equal) (less)
        elif op == 0x12:
            [a, b], stack = get_n_of_stack_elements(2, stack)
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
        
        # SGT (equal) (greater)
        elif op == 0x13:
            [a, b], stack = get_n_of_stack_elements(2, stack)
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
        
        # EQ (not equal)
        elif op == 0x14:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            if a - b == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)

        # ISZERO (not zero) (zero)
        elif op == 0x15:
            [a], stack = get_n_of_stack_elements(1, stack)
            if a == 0:
                stack.insert(0, 1)
            else:
                stack.insert(0, 0)
        
        # AND
        elif op == 0x16:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = a & b
            stack.insert(0, value)
        
        # OR
        elif op == 0x17:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = a | b
            stack.insert(0, value)
        
        # XOR
        elif op == 0x18:
            [a, b], stack = get_n_of_stack_elements(2, stack)
            value = a ^ b
            stack.insert(0, value)

        # NOT
        elif op == 0x19:
            [a], stack = get_n_of_stack_elements(1, stack)
            value = MAX_UINT256 - a
            stack.insert(0, value)
        
        # BYTE
        elif op == 0x1a:
            [byte_offset, num], stack = get_n_of_stack_elements(2, stack)
            if byte_offset > 31 or byte_offset < 0: # (out of range)
                stack.insert(0, 0)
            else:
                high_bit_mask = (0x1 << ((32 - byte_offset) * 8)) - 1
                low_bit_mask = (0x1 << ((32 - byte_offset - 1) * 8)) - 1 if 32 - byte_offset - 1 > 0 else 0
                bit_mask = high_bit_mask ^ low_bit_mask
                value = (num & bit_mask) >> (32 - byte_offset - 1) * 8
                stack.insert(0, value)

        # SHL (discards) (too large)
        elif op == 0x1b:
            [shift, num], stack = get_n_of_stack_elements(2, stack)
            num_is_negative, num_byte_size = is_num_negative(num)
            if shift >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards)
                value = extract_lower_bits(num, num_byte_size * BYTE_SIZE - shift) << shift
                stack.insert(0, value)

        # SHR (discards) (too large)
        elif op == 0x1c:
            [shift, num], stack = get_n_of_stack_elements(2, stack)
            num_is_negative, num_byte_size = is_num_negative(num)
            if shift >= MAX_UINT32: # (too large)
                stack.insert(0, 0)
            else: # (discards) 
                value = num >> shift
                stack.insert(0, value)

        # SAR (fills 1s) (too large) (positive, too large)
        elif op == 0x1d:
            [shift, num], stack = get_n_of_stack_elements(2, stack)
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

        # SHA3
        elif op == 0x20:
            [byte_offset, byte_size], stack = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + byte_size:
                memory += ([0] * (byte_offset + 32 - len(memory)))
            value = 0
            for i in range(byte_size):
                value = value << BYTE_SIZE
                value += memory[byte_offset + i]
            hashed_value = int.from_bytes(keccak(value.to_bytes(byte_size, byteorder='big')), byteorder="big")
            stack.insert(0, hashed_value)

        # ADDRESS
        elif op == 0x30:
            address = int(tx['to'], 16)
            stack.insert(0, address)

        # BALANCE
        elif op == 0x31:
            [address], stack = get_n_of_stack_elements(1, stack)
            if state is not None and hex(address) in state:
                balance = int(state[hex(address)]["balance"], 16)
                stack.insert(0, balance)
            else:
                stack.insert(0, 0)
        
        # ORIGIN
        elif op == 0x32:
            address = int(tx['origin'], 16)
            stack.insert(0, address)

        # CALLER
        elif op == 0x33:
            address = int(tx['from'], 16)
            stack.insert(0, address)
        
        # CALLVALUE
        elif op == 0x34:
            value = int(tx['value'], 16)
            stack.insert(0, value)
        
        # CALLDATALOAD
        elif op == 0x35:
            [byte_offset], stack = get_n_of_stack_elements(1, stack)
            data = int(tx['data'], 16)
            data = (data << (BYTE_SIZE * byte_offset)) & ((0x1 << 256) - 1) # (tail)
            stack.insert(0, data)

        # CALLDATASIZE
        elif op == 0x36:
            if tx is not None:
                data = int(tx.get('data', 0), 16)
                count = 1
                while data > 0:
                    data = data >> BYTE_SIZE
                    count += 1
                stack.insert(0, count)
            else:
                stack.insert(0, 0)

        # CALLDATACOPY
        elif op == 0x37:
            [dest_offset, byte_offset, byte_size], stack = get_n_of_stack_elements(3, stack)
            data = int(tx['data'], 16)
            bit_mask = ((0x1 << 256) - 1) ^ ((0x1 << (256 - byte_size * 8)) - 1)
            data = (data << (BYTE_SIZE * byte_offset)) & bit_mask # (tail)
            if len(memory) < dest_offset + 32: # (tail)
                memory += [0] * (dest_offset + 32 - len(memory))
            for i in range(32):
                memory[dest_offset + 31 - i] = (data >> (i * 8)) & 0xFF

        # CODESIZE (small)
        elif op == 0x38:
            stack.insert(0, len(code))
        
        # CODECOPY
        elif op == 0x39:
            [dest_offset, byte_offset, byte_size], stack = get_n_of_stack_elements(3, stack)
            if len(memory) < dest_offset + byte_size:
                memory += ([0] * (dest_offset + byte_size - len (memory)))
            data = code
            for i in range(byte_size):
                if (byte_offset + i) < len(data):
                    memory[dest_offset + i] = data[byte_offset + i]
                else:
                    memory[dest_offset + i] = 0

        # GASPRICE
        elif op == 0x3a:
            gasprice = int(tx['gasprice'], 16)
            stack.insert(0, gasprice)
        
        # EXTCODESIZE
        elif op == 0x3b:
            [address], stack = get_n_of_stack_elements(1, stack)
            address = padding_address(hex(address))
            if state is None or address not in state or 'code' not in state[address]:
                stack.insert(0, 0)
            else:
                stack.insert(0, len(state[address]['code']['bin']) / 2)
        
        # EXTCODECOPY
        elif op == 0x3c:
            [address, dest_offset, byte_offset, byte_size], stack = get_n_of_stack_elements(4, stack)
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

        # RETURNDATASIZE
        elif op == 0x3d:
            if last_ret:
                stack.insert(0, len(last_ret) / 2)
            else:
                stack.insert(0, 0)

        # EXTCODEHASH
        elif op == 0x3f:
            [address], stack = get_n_of_stack_elements(1, stack)
            address = padding_address(hex(address))
            if state is None or address not in state or 'code' not in state[address]:
                stack.insert(0, 0)
            else:
                extcode = bytes.fromhex(state[address]['code']['bin'])
                stack.insert(0, int.from_bytes(keccak(extcode), byteorder='big'))

        # BLOCKHASH
        elif op == 0x40:
            pass

        # COINBASE
        elif op == 0x41:
            coinbase = int(block['coinbase'], 16)
            stack.insert(0, coinbase)
        
        # TIMESTAMP
        elif op == 0x42:
            timestamp = int(block['timestamp'], 16)
            stack.insert(0, timestamp)
        
        # BLOCKNUMBER
        elif op == 0x43:
            blocknumber = int(block['number'], 16)
            stack.insert(0, blocknumber)

        # DIFFICULTY
        elif op == 0x44:
            difficulty = int(block['difficulty'], 16)
            stack.insert(0, difficulty)

        # GASLIMIT
        elif op == 0x45:
            gaslimit = int(block['gaslimit'], 16)
            stack.insert(0, gaslimit)
        
        # CHAINID
        elif op == 0x46:
            chainid = int(block['chainid'], 16)
            stack.insert(0, chainid)
        
        # SELFBALANCE
        elif op == 0x47:
            address = tx["to"]
            if state is None or address not in state or 'balance' not in state[address]:
                stack.insert(0, 0)
            else:
                stack.insert(0, int(state[address]['balance'], 16))

        # BASEFEE
        elif op == 0x48:
            basefee = int(block['basefee'], 16)
            stack.insert(0, basefee)

        # POP
        elif op == 0x50:
            result, stack = get_n_of_stack_elements(1, stack)
            success = True
        
        # MLOAD
        elif op == 0x51:
            [byte_offset], stack = get_n_of_stack_elements(1, stack)
            data = mload(memory, byte_offset, 32)
            stack.insert(0, data)

        # MSTORE
        elif op == 0x52:
            [byte_offset, num], stack = get_n_of_stack_elements(2, stack)
            mstore(memory, num, byte_offset, 32)

        # MSTORE8
        elif op == 0x53:
            [byte_offset, num], stack = get_n_of_stack_elements(2, stack)
            if len(memory) < byte_offset + 1:
                memory += [0] * (byte_offset + 1 - len(memory))
            memory[byte_offset] = num & 0xff

        # SLOAD
        elif op == 0x54:
            [key], stack = get_n_of_stack_elements(1, stack)
            stack.insert(0, storage.get(hex(key), 0))
        
        # SSTORE
        elif op == 0x55:
            [key, value], stack = get_n_of_stack_elements(2, stack)
            storage[hex(key)] = value

        # JUMP
        elif op == 0x56:
            [counter], stack = get_n_of_stack_elements(1, stack)
            if code[counter] == 0x5b and not is_invalid_JUMPDEST(counter):
                pc = counter
                continue
            else:
                success = False
                break
        
        # JUMPI
        elif op == 0x57:
            [counter, b], stack = get_n_of_stack_elements(2, stack)
            if b == 0:
                pass
            else:
                if code[counter] == 0x5b and not is_invalid_JUMPDEST(counter):
                    pc = counter
                    continue
                else:
                    success = False
                    break
        
        # PC
        elif op == 0x58:
            stack.insert(0, pc)

        # MSIZE
        elif op == 0x59:
            value = math.ceil(len(memory) / 32) * 32
            stack.insert(0, value)

        # GAS
        elif op == 0x5a:
            stack.insert(0, MAX_UINT256)
        
        # JUMPDEST
        elif op == 0x5b:
            pass

        # PUSH0
        elif op == 0x5f:
            stack.insert(0, 0)
            
        # PUSH1 - PUSH32
        elif op >= 0x60 and op <= 0x7f:
            size = op - 0x60
            value = 0
            while size >= 0:
                pc += 1
                value = value | code[pc] << size * BYTE_SIZE
                size -= 1
            stack.insert(0, value)

        # DUP1 - 16
        elif op >= 0x80 and op <= 0x8f:
            index = op - 0x80
            num = stack[index]
            stack.insert(0, num)
        
        # SWAP1 - 16
        elif op >= 0x90 and op <= 0x9f:
            index = op - 0x90 + 1
            num = stack[index]
            stack[index] = stack[0]
            stack[0] = num
        
        # LOG0 - 4
        elif op >= 0xa0 and op <= 0xa4:
            [byte_offset, byte_size], stack = get_n_of_stack_elements(2, stack)
            log_num = op - 0xa0
            if log_num != 0:
                topics, stack = get_n_of_stack_elements(log_num, stack)
                topics = [hex(ele) for ele in topics]
            else:
                topics = []
            if len(memory) < byte_offset + 32:
                memory += ([0] * (byte_offset + 32 - len(memory)))
            data = 0
            for i in range(byte_size):
                data = data << BYTE_SIZE
                data += memory[byte_offset + i]
            data = hex(data)[2:]
            logs.append({
                "address": tx['to'],
                "data": data,
                "topics": topics
            })

        # CALL
        elif op == 0xf1:
            [gas, address, value, args_offset, args_size, ret_offset, ret_size], stack = get_n_of_stack_elements(7, stack)
            address = padding_address(hex(address))
            args = mload(memory, args_offset, args_size)
            new_tx = {
                "to": address,
                "value": value,
                "origin": tx.get("origin") if tx else None,
                "from": tx.get("to") if tx else None,
            }
            _success, _, new_logs, new_ret = evm(bytes.fromhex(state[address]['code']['bin']), new_tx, block, state)
            logs += new_logs
            new_ret = new_ret[:ret_size * 2]
            if len(new_ret) != 0:
                memory = mstore(memory, int(new_ret, 16), ret_offset, ret_size)
                last_ret = new_ret
            stack.insert(0, int(_success))

        # RETURN
        elif op == 0xf3:
            [byte_offset, byte_size], stack = get_n_of_stack_elements(2, stack)
            data = mload(memory, byte_offset, byte_size)
            ret = hex(data)[2:]
            break
            
        # REVERT
        elif op == 0xfd:
            [byte_offset, byte_size], stack = get_n_of_stack_elements(2, stack)
            data = mload(memory, byte_offset, byte_size)
            ret = hex(data)[2:]
            success = False
            break

        # INVALID
        elif op == 0xfe:
            success = False
            break
        
        pc += 1

    return (success, stack, logs, ret)

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
            (success, stack, logs, ret) = evm(code, tx, block, state)

            expected_stack = [int(x, 16) for x in test['expect'].get('stack', [])]
            expected_logs = test['expect'].get('logs', [])
            expected_return = test['expect'].get("return", None)


            if stack != expected_stack or success != test['expect']['success'] or expected_logs != logs or expected_return != ret:
                print(f"❌ Test #{i + 1}/{total} {test['name']}")
                if stack != expected_stack:
                    print("Stack doesn't match")
                    print(" expected in decimal:", expected_stack)
                    print("   actual in decimal:", stack)
                    print(" expected in hex:", [hex(expected) for expected in expected_stack])
                    print("   actual in hex:", [hex(ele) for ele in stack])
                elif expected_logs != logs:
                    print("Log doesn't match")
                    print(" expected:", expected_logs)
                    print("   actual:", logs)
                elif expected_return != ret:
                    print("Return doesn't match")
                    print(" expected:", expected_return)
                    print("   actual:", ret)
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
