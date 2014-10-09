-------------------------------------------------------------------------------
-- Title      : RTLTopModuleVHDL
-- Project    : 
-------------------------------------------------------------------------------
-- File       : RTLTopModuleVHDL.vhdl
-- Author     : Adrian Fiergolski  <Adrian.Fiergolski@cern.ch>
-- Company    : CERN
-- Created    : 2014-09-26
-- Last update: 2014-09-26
-- Platform   : 
-- Standard   : VHDL'2008
-------------------------------------------------------------------------------
-- Description: The module to test HDLMake
-------------------------------------------------------------------------------
-- Copyright (c) 2014 CERN    
--
-- This file is part of .
--
--  is free firmware: you can redistribute it and/or modify it under the terms of the GNU General Public License 
-- as published by the Free Software Foundation, either version 3 of the License, or any later version.
--
--  is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied 
-- warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License along with . If not, see http://www.gnu.org/licenses/.

-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 2014-09-26  1.0      afiergol	Created
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity RTLTopModuleVHDL is

end entity RTLTopModuleVHDL;

architecture Behavioral of RTLTopModuleVHDL is
  signal probe : STD_LOGIC;
begin  -- architecture Behavioral

  probe <= '1';

end architecture Behavioral;
