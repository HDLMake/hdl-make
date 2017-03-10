-------------------------------------------------------
-- Design      : Simple 8-bit VHDL counter
-- Author      : Javier D. Garcia-Lasheras
-------------------------------------------------------
	
library ieee ;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-------------------------------------------------------

entity counter is

generic (cycles_per_second : unsigned := 12000000);

port(	
    clock:  in std_logic;
    clear:  in std_logic;
    count:  in std_logic;
    Q:	    out std_logic_vector(7 downto 0)
);
end counter;

-------------------------------------------------------

architecture behv of counter is		 	  
    signal ready: std_logic;
    signal Pre_Q: unsigned(7 downto 0);
    signal divider: unsigned(23 downto 0);

begin

    process(clock, count, clear)
    begin
	if (clock='1' and clock'event) then
            if ready = '1' then
                if divider = cycles_per_second then
                    divider <= (others => '0');
                    Pre_Q(7 downto 1) <= Pre_Q(6 downto 0);
                    Pre_Q(0) <= Pre_Q(7);
                else
                    divider <= divider + 1;
                end if;
            else
                ready <= '1';
                Pre_Q <= "00010001";
                divider <= (others => '0');
            end if;
	end if;
    end process;
	
    Q <= std_logic_vector(Pre_Q);

end behv;

-------------------------------------------------------
