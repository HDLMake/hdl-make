-----------------------------------------------------------------------
-- Design  : Counter VHDL top module, Avnet Zedboard Starter Kit
-- Author  : Javier D. Garcia-Lasheras
-----------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;			 
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

entity zedboard_top is
  port (
    clear_i: in std_logic;
    count_i: in std_logic;
    clock_i: in std_logic;
    led_o: out std_logic_vector(7 downto 0)
  );
end zedboard_top;

-----------------------------------------------------------------------

architecture structure of zedboard_top is

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
  s_clear <= clear_i;
  s_count <= count_i;
  led_o <= s_Q; 
  
end architecture structure;

----------------------------------------------------------------
