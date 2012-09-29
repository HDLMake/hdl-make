library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.gencores_pkg.all;

entity top_module_tb is				-- entity declaration
end top_module_tb;

architecture sim of top_module_tb is

	-- 100.00 MHz clock
	constant c_clk_period					: time := 10.00 ns;
	constant c_sim_time						: time := 1000.00 ns;
	
	signal g_end_simulation          		: boolean   := false; -- Set to true to halt the simulation

	signal clk100							: std_logic := '0';
	signal s_locked							: std_logic;
	signal s_blink							: std_logic_vector(7 downto 0);

	-- Components
	component top_module
	port(
		clk_i								: in std_logic;
		locked_i							: in std_logic;
		blink_o								: out std_logic_vector(7 downto 0)
	);
	end component;

	-- Functions
	--function calculate_next_input_sample(sample_number : in integer) return std_logic_vector is
   -- variable A      : real  := 1.0;   -- Amplitude for wave
   -- variable F      : real  := 100.0;   -- Frequency for wave
   -- variable P      : real  := 0.0;   -- Phase for wave
   -- variable theta  : real;

   -- variable y      : real;     -- The calculated value as a real
   -- variable y_int  : integer;  -- The calculated value as an integer
   -- variable result : std_logic_vector(c_ip_width-1 downto 0);
       
   -- variable number_of_samples : real := 100.0 * real(47);

  --begin
   -- theta  := (2.0 * MATH_PI * F * real(sample_number mod integer(number_of_samples))) / number_of_samples;
 
    --y      := A * sin(theta + P);
    --y_int  := integer(round(y * real(2**(c_ip_width-2))));
    --result := std_logic_vector(to_signed(y_int, c_ip_width));

    --return result;
  --end function calculate_next_input_sample;
	
begin

	cmp_top_module : top_module
	port map
	(
		clk_i							=> clk100,
		locked_i						=> s_locked,
		blink_o							=> s_blink
	);

	--p_locked : process
	--begin
	--	s_locked                    <= '0';
	--	wait for 20 ns;
		--wait until rising_edge(clk100);
		--wait until rising_edge(clk100);
		--wait until rising_edge(clk100);
	--	s_locked                    <= '1';
	--end process p_locked;
	
	p_clk_gen : process is
	begin
		while g_end_simulation = false loop
			wait for c_clk_period/2;
			clk100 <= not clk100;
			wait for c_clk_period/2;
			clk100 <= not clk100;	
		end loop;
		wait;  -- simulation stops here
	end process p_clk_gen;
	
	p_main_simulation : process is
	begin
	--	wait for c_sim_time;
	--	g_end_simulation <= true;
	--	wait;
		s_locked <= '0';
		wait for 2*c_clk_period;
		s_locked <= '1';
		wait for 100*c_clk_period;

		-- End simualtion
		g_end_simulation <= true;
	end process p_main_simulation;

end sim;
