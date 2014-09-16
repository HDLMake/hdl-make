----------------------------------------------------------
-- Design  : Counter VHDL top module, Lattice Brevia2
-- Author  : Javier D. Garcia-Lasheras
----------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;			 
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

entity brevia2_top is
  port (
    clear_i: in std_logic;
    count_i: in std_logic;
    clock_i: in std_logic;
    clken_o: out std_logic;
    led_o: out std_logic_vector(7 downto 0)
  );
end brevia2_top;

----------------------------------------------------------

architecture structure of brevia2_top is

  component counter
    port (   
      clock: in std_logic;
      clear: in std_logic;
      count: in std_logic;
      Q: out std_logic_vector(7 downto 0)
    );
  end component;

  signal s_clock: std_logic;
  signal s_clear: std_logic;
  signal s_count: std_logic;
  signal s_Q: std_logic_vector(7 downto 0);

begin
    
  U_counter: counter 
    port map (
      clock => s_clock, 
      clear => s_clear, 
      count => s_count, 
      Q => s_Q
    );
	
  s_clock <= clock_i;
  clken_o <= '1';
  s_clear <= not clear_i;
  s_count <= not count_i;
  led_o <= not s_Q; 
  
end architecture structure;

----------------------------------------------------------------
