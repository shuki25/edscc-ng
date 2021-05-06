# ************************************************************
# Sequel Ace SQL dump
# Version 3028
#
# https://sequel-ace.com/
# https://github.com/Sequel-Ace/Sequel-Ace
#
# Host: db (MySQL 5.7.32-0ubuntu0.16.04.1-log)
# Database: edscc-ng
# Generation Time: 2021-05-06 01:19:07 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE='NO_AUTO_VALUE_ON_ZERO', SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

DROP TABLE IF EXISTS `access_history`;
DROP TABLE IF EXISTS `acl`;
DROP TABLE IF EXISTS `activity_counter`;
DROP TABLE IF EXISTS `announcement`;
DROP TABLE IF EXISTS `capi_log`;
DROP TABLE IF EXISTS `carousel`;
DROP TABLE IF EXISTS `commander`;
DROP TABLE IF EXISTS `commander_info`;
DROP TABLE IF EXISTS `community_goal`;
DROP TABLE IF EXISTS `crime`;
DROP TABLE IF EXISTS `crime_type`;
DROP TABLE IF EXISTS `custom_rank`;
DROP TABLE IF EXISTS `debug`;
DROP TABLE IF EXISTS `earning_history`;
DROP TABLE IF EXISTS `earning_type`;
DROP TABLE IF EXISTS `edmc`;
DROP TABLE IF EXISTS `error_log`;
DROP TABLE IF EXISTS `faction`;
DROP TABLE IF EXISTS `faction_activity`;
DROP TABLE IF EXISTS `galnet_news`;
DROP TABLE IF EXISTS `journal_log`;
DROP TABLE IF EXISTS `language`;
DROP TABLE IF EXISTS `minor_faction`;
DROP TABLE IF EXISTS `motd`;
DROP TABLE IF EXISTS `power`;
DROP TABLE IF EXISTS `rank`;
DROP TABLE IF EXISTS `read_history`;
DROP TABLE IF EXISTS `squadron`;
DROP TABLE IF EXISTS `squadron_tags`;
DROP TABLE IF EXISTS `status`;
DROP TABLE IF EXISTS `tags`;
DROP TABLE IF EXISTS `thargoid_activity`;
DROP TABLE IF EXISTS `thargoid_variant`;
DROP TABLE IF EXISTS `user_profile`;

DELETE FROM django_migrations where app in ('core', 'squadron', 'commander');


/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
