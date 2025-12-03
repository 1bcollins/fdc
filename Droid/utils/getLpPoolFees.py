from decimal import Decimal

# Constants
ZERO = 0
Q128 = 2 ** 128
Q256 = 2 ** 256

# Overflow-safe subtraction function
def sub_in_256(x, y):
    difference = x - y
    if difference < 0:
        return Q256 + difference
    return difference

# Convert to big number
def to_big_number(value):
    return int(value)

# Adjust for decimals
def adjust_for_decimals(value, decimals):
    return Decimal(value) / Decimal(10 ** decimals)

def get_fees(fee_growth_global0, fee_growth_global1, fee_growth0_low, fee_growth0_hi, 
             fee_growth_inside0, fee_growth1_low, fee_growth1_hi, fee_growth_inside1, 
             liquidity, decimals0, decimals1, tick_lower, tick_upper, tick_current):
    
    # Convert all inputs to big integers if they are not already
    fee_growth_global_0 = to_big_number(fee_growth_global0)
    fee_growth_global_1 = to_big_number(fee_growth_global1)
    tick_lower_fee_growth_outside_0 = to_big_number(fee_growth0_low)
    tick_lower_fee_growth_outside_1 = to_big_number(fee_growth1_low)
    tick_upper_fee_growth_outside_0 = to_big_number(fee_growth0_hi)
    tick_upper_fee_growth_outside_1 = to_big_number(fee_growth1_hi)
    fee_growth_inside_last_0 = to_big_number(fee_growth_inside0)
    fee_growth_inside_last_1 = to_big_number(fee_growth_inside1)

    # Initialize fee growth variables
    tick_lower_fee_growth_below_0 = ZERO
    tick_lower_fee_growth_below_1 = ZERO
    tick_upper_fee_growth_above_0 = ZERO
    tick_upper_fee_growth_above_1 = ZERO

    # Calculate upper and lower fee growth based on tick position
    if tick_current >= tick_upper:
        tick_upper_fee_growth_above_0 = sub_in_256(fee_growth_global_0, tick_upper_fee_growth_outside_0)
        tick_upper_fee_growth_above_1 = sub_in_256(fee_growth_global_1, tick_upper_fee_growth_outside_1)
    else:
        tick_upper_fee_growth_above_0 = tick_upper_fee_growth_outside_0
        tick_upper_fee_growth_above_1 = tick_upper_fee_growth_outside_1

    if tick_current >= tick_lower:
        tick_lower_fee_growth_below_0 = tick_lower_fee_growth_outside_0
        tick_lower_fee_growth_below_1 = tick_lower_fee_growth_outside_1
    else:
        tick_lower_fee_growth_below_0 = sub_in_256(fee_growth_global_0, tick_lower_fee_growth_outside_0)
        tick_lower_fee_growth_below_1 = sub_in_256(fee_growth_global_1, tick_lower_fee_growth_outside_1)

    # Calculate fee growth for token0 and token1
    fee_growth_token0 = sub_in_256(sub_in_256(fee_growth_global_0, tick_lower_fee_growth_below_0), tick_upper_fee_growth_above_0)
    fee_growth_token1 = sub_in_256(sub_in_256(fee_growth_global_1, tick_lower_fee_growth_below_1), tick_upper_fee_growth_above_1)

    # Uncollected fees formula
    uncollected_fees_0 = (liquidity * sub_in_256(fee_growth_token0, fee_growth_inside_last_0)) / Q128
    uncollected_fees_1 = (liquidity * sub_in_256(fee_growth_token1, fee_growth_inside_last_1)) / Q128

    # Adjust and format for output
    uncollected_fees_adjusted_0 = adjust_for_decimals(uncollected_fees_0, decimals0)
    uncollected_fees_adjusted_1 = adjust_for_decimals(uncollected_fees_1, decimals1)

    # Output with scientific notation for better readability on small values
    #print(f"Amount fees token 0 in lowest decimal: {uncollected_fees_0:e}")
    #print(f"Amount fees token 1 in lowest decimal: {uncollected_fees_1:e}")
    #print(f"Amount fees token 0 Human format: {uncollected_fees_adjusted_0:.10f}")
    #print(f"Amount fees token 1 Human format: {uncollected_fees_adjusted_1:.10f}")

    return {
        "uncollected_fees_token0": uncollected_fees_adjusted_0,
        "uncollected_fees_token1": uncollected_fees_adjusted_1
    }

'''
# Example:
result = get_fees(
    fee_growth_global0="3094836483914812667943230173936420",
    fee_growth_global1="200000000000000000000",
    fee_growth0_low="5000000000000000000",
    fee_growth0_hi="10000000000000000000",
    fee_growth_inside0="1000000000000000000",
    fee_growth1_low="2500000000000000000",
    fee_growth1_hi="5000000000000000000",
    fee_growth_inside1="2000000000000000000",
    liquidity=1255202553895193,
    decimals0=18,
    decimals1=18,
    tick_lower=-198180,
    tick_upper=-196860,
    tick_current=-197500
)

print(result)
'''

