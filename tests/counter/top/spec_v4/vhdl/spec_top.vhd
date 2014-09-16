-----------------------------------------------------------------------
-- Design  : Counter VHDL top module, SPEC (Simple PCIe Carrier)
-- Author  : Javier D. Garcia-Lasheras
-----------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

library UNISIM;
use UNISIM.vcomponents.all;


entity spec_top is
  port (
    clear_i: in std_logic;
    count_i: in std_logic;
    clock_i: in std_logic;
    led_o: out std_logic_vector(3 downto 0)
  );
end spec_top;

-----------------------------------------------------------------------

architecture structure of spec_top is

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
  s_clear <= not clear_i;
  s_count <= not count_i;
  led_o(3 downto 0) <= not s_Q(7 downto 4); 
  
end architecture structure;

-----------------------------------------------------------------------

