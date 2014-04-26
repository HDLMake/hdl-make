library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity myfilter is
    port (
        clk : in std_logic;
        rst : in std_logic;
        sig_in : in signed(15 downto 0);
        sig_out : out signed(15 downto 0)
    );
end entity;

architecture Direct_Form_I_Transposed of myfilter is

-- This file has been generated with Libre-FDATool
-- Creation Time: 2014-04-26 01:36


-- Z^-1 delay blocks
type zb_array is array (0 to 6) of signed(30 downto 0);
signal zb, zb_next: zb_array;


-- Filter constants
type b_array is array (0 to 7) of signed(15 downto 0);
signal b: b_array;

-- Filter Adders
type sum_b_array is array (0 to 6) of signed(30 downto 0);
signal sb: sum_b_array;

-- Filter Products
type product_b_array is array (0 to 7) of signed(30 downto 0);
signal pb: product_b_array;
type product_b_temp_array is array (0 to 7) of signed(31 downto 0);
signal pb_temp: product_b_temp_array;

-- Feedback loop accumulator
signal v: signed(15 downto 0);

-- Begin Architecture
begin

-- Assign Coefficients
b(0) <= "0000111000100010"; -- 0.110401
b(1) <= "0000111110110011"; -- 0.122661
b(2) <= "0001000011001101"; -- 0.131255
b(3) <= "0001000101011110"; -- 0.135682
b(4) <= "0001000101011110"; -- 0.135682
b(5) <= "0001000011001101"; -- 0.131255
b(6) <= "0000111110110011"; -- 0.122661
b(7) <= "0000111000100010"; -- 0.110401



----------------------------------
-- Sequential logic description --
----------------------------------

-- Sequential delay chain for the B block
seq_b_block: for x in 0 to 6 generate
    reg_b: process (clk)
    begin
        if (clk'event and clk = '1') then
            if (rst = '1') then
                zb(x) <=  (others => '0');
            else
                zb(x) <=  zb_next(x);
            end if;
        end if;
    end process reg_b;
end generate seq_b_block;





----------------------------------
-- Processing logic description --
----------------------------------

-- Bypassing the A processing block
v <= sig_in;

-- Processing block for the Filter structure B side
 process_b_block: for n in 0 to 7 generate
    -- Calculate products being generated
    pb_temp(n) <= v * b(n);
    pb(n) <= pb_temp(n)(30 downto 0);
    -- Calculate sums being generated
    add_b_block: if (n < 7) generate
        sb(n) <= pb(n) + zb(n);
    end generate add_b_block;
    -- Calculate values for zb_next
    -- ... those halfway in the loop
    mid_b_tap: if (n < 6) generate
        zb_next(n) <= sb(n+1);
    end generate mid_b_tap;
    -- ... final structure
    final_b_tap: if (n = 6) generate
        zb_next(n) <= pb(n+1);
    end generate final_b_tap;
end generate process_b_block;

-- Convert Fixed Point to sig_out from sb(0)
sig_out(15 downto 15) <= sb(0)(30 downto 30);
sig_out(14 downto 0) <= sb(0)(29 downto 15);

end Direct_Form_I_Transposed;
