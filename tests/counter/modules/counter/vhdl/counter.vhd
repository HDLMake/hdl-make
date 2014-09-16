-------------------------------------------------------
-- Design      : Simple 8-bit VHDL counter
-- Author      : Javier D. Garcia-Lasheras
-------------------------------------------------------
	
library ieee ;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-------------------------------------------------------

entity counter is

port(	
    clock:  in std_logic;
    clear:  in std_logic;
    count:  in std_logic;
    Q:	    out std_logic_vector(7 downto 0)
);
end counter;

-------------------------------------------------------

architecture behv of counter is		 	  
	
    signal Pre_Q: unsigned(7 downto 0);

begin

    process(clock, count, clear)
    begin
	if clear = '1' then
 	    Pre_Q <= "00000000";
	elsif (clock='1' and clock'event) then
	    if count = '1' then
			Pre_Q <= Pre_Q + 1;
	    end if;
	end if;
    end process;
	
    Q <= std_logic_vector(Pre_Q);

end behv;

-------------------------------------------------------
