library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library work;
use work.gencores_pkg.all;

entity top_module is
	port(
		clk_i	                    : in std_logic;
		locked_i					: in std_logic;
        blink_o                     : out std_logic_vector(7 downto 0)
	);
end top_module;

architecture rtl of top_module is
    -- Constant declaration
    constant c_blink_num_pins       : natural := 8;
    constant c_counter_width        : natural := 4;

    -- Global clock and reset signals
	--signal s_locked 				: std_logic;
	signal clk_sys_rstn 			: std_logic;

	-- Only one clock domain
	signal reset_clks 				: std_logic_vector(0 downto 0);
	signal reset_rstn 				: std_logic_vector(0 downto 0);

	-- Global Clock Single ended
	signal clk_sys  				: std_logic;

    -- Counter signal
	signal s_counter				: unsigned(c_counter_width-1 downto 0);
	constant s_counter_full			: integer := 4;

    signal s_blink					: std_logic_vector(c_blink_num_pins-1 downto 0);
begin
    -- Reset synchronization
	cmp_reset : gc_reset
	generic map(
		g_logdelay					=> 1,
		g_syncdepth					=> 2
	)
	port map(
		free_clk_i 			        => clk_sys,
		locked_i   			        => locked_i,
		clks_i     			        => reset_clks,
		rstn_o     			        => reset_rstn
	);

	-- Simulation only
	clk_sys		                    <= clk_i;
	-- End of simulation only!
	reset_clks(0)                   <= clk_sys;
	clk_sys_rstn                    <= reset_rstn(0);

    p_counter : process (clk_sys)
	begin
	    if rising_edge(clk_sys) then
			if clk_sys_rstn = '0' then
				s_counter			<= (others => '0');
				s_blink				<= x"01";
			else
				if (s_counter = s_counter_full-1) then
					s_counter		<= (others => '0');
					s_blink			<= s_blink(c_blink_num_pins-2 downto 0) & s_blink(c_blink_num_pins-1);
				else
					s_counter		<= s_counter + 1;
				end if;
			end if;
		end if;
	end process;

	blink_o						<= s_blink;


end rtl;
