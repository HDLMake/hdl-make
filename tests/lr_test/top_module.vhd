library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

entity top_module is
  generic(
    g_clk_period                            : natural := 100000000;
    g_sim                                   : boolean := true
  );
  port(
    clk_i                                   : in std_logic;
    rst_n_i                                 : in std_logic;
    blink_o                                 : out std_logic_vector(7 downto 0)
  );
end top_module;

architecture rtl of top_module is

  function f_ceil_log2(x : natural) return natural is
  begin
    if x <= 1 then
      return 0;
    else
      return f_ceil_log2((x+1)/2) + 1;
    end if;
  end f_ceil_log2;

  -- Constant declaration
  constant c_blink_num_pins                 : natural := 8;
  constant c_counter_width                  : natural := f_ceil_log2(c_blink_num_pins);
  constant c_counter_full                   : natural := c_blink_num_pins;
  constant c_sim_clk_period                 : natural := 1;
  constant c_clk_period                     : natural := g_clk_period;

  -- Global clock
  signal clk_sys                            : std_logic;

  -- Counter signal
  signal s_counter                          : unsigned(c_counter_width-1 downto 0);
  signal s_counter_full                     : unsigned(c_counter_width-1 downto 0);

  signal s_blink                            : std_logic_vector(c_blink_num_pins-1 downto 0);
  signal rst_n                              : std_logic;
begin

  clk_sys                                   <= clk_i;
  rst_n                                     <= rst_n_i;

  gen_sim_clk_period : if g_sim = true generate
    s_counter_full <= to_unsigned(c_sim_clk_period, c_counter_width);
  end generate;

  gen_syn_clk_period : if g_sim = false generate
    s_counter_full <= to_unsigned(c_clk_period, c_counter_width);
  end generate;

  p_counter : process (clk_sys)
  begin
    if rising_edge(clk_sys) then
      if rst_n = '0' then
        s_counter     <= (others => '0');
        s_blink       <= x"01";
      else
        if (s_counter = s_counter_full-1) then
          s_counter   <= (others => '0');
          s_blink     <= s_blink(c_blink_num_pins-2 downto 0) & s_blink(c_blink_num_pins-1);
        else
          s_counter   <= s_counter + 1;
        end if;
      end if;
    end if;
  end process;

  blink_o                                   <= s_blink;

end rtl;
