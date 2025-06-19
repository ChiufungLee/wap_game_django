-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: wap_game_db
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=133 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add 游戏城市',7,'add_gamecity'),(26,'Can change 游戏城市',7,'change_gamecity'),(27,'Can delete 游戏城市',7,'delete_gamecity'),(28,'Can view 游戏城市',7,'view_gamecity'),(29,'Can add 游戏页面',8,'add_gamepage'),(30,'Can change 游戏页面',8,'change_gamepage'),(31,'Can delete 游戏页面',8,'delete_gamepage'),(32,'Can view 游戏页面',8,'view_gamepage'),(33,'Can add 帮派',9,'add_gang'),(34,'Can change 帮派',9,'change_gang'),(35,'Can delete 帮派',9,'delete_gang'),(36,'Can view 帮派',9,'view_gang'),(37,'Can add 聊天消息',10,'add_chatmessage'),(38,'Can change 聊天消息',10,'change_chatmessage'),(39,'Can delete 聊天消息',10,'delete_chatmessage'),(40,'Can view 聊天消息',10,'view_chatmessage'),(41,'Can add 游戏事件',11,'add_gameevent'),(42,'Can change 游戏事件',11,'change_gameevent'),(43,'Can delete 游戏事件',11,'delete_gameevent'),(44,'Can view 游戏事件',11,'view_gameevent'),(45,'Can add 游戏地图',12,'add_gamemap'),(46,'Can change 游戏地图',12,'change_gamemap'),(47,'Can delete 游戏地图',12,'delete_gamemap'),(48,'Can view 游戏地图',12,'view_gamemap'),(49,'Can add 地图区域',13,'add_gamemaparea'),(50,'Can change 地图区域',13,'change_gamemaparea'),(51,'Can delete 地图区域',13,'delete_gamemaparea'),(52,'Can view 地图区域',13,'view_gamemaparea'),(53,'Can add 游戏NPC',14,'add_gamenpc'),(54,'Can change 游戏NPC',14,'change_gamenpc'),(55,'Can delete 游戏NPC',14,'delete_gamenpc'),(56,'Can view 游戏NPC',14,'view_gamenpc'),(57,'Can add item',15,'add_item'),(58,'Can change item',15,'change_item'),(59,'Can delete item',15,'delete_item'),(60,'Can view item',15,'view_item'),(61,'Can add 页面组件',16,'add_pagecomponent'),(62,'Can change 页面组件',16,'change_pagecomponent'),(63,'Can delete 页面组件',16,'delete_pagecomponent'),(64,'Can view 页面组件',16,'view_pagecomponent'),(65,'Can add 玩家',17,'add_player'),(66,'Can change 玩家',17,'change_player'),(67,'Can delete 玩家',17,'delete_player'),(68,'Can view 玩家',17,'view_player'),(69,'Can add 帮派成员',18,'add_gangmember'),(70,'Can change 帮派成员',18,'change_gangmember'),(71,'Can delete 帮派成员',18,'delete_gangmember'),(72,'Can view 帮派成员',18,'view_gangmember'),(73,'Can add 帮派申请',19,'add_gangapplication'),(74,'Can change 帮派申请',19,'change_gangapplication'),(75,'Can delete 帮派申请',19,'delete_gangapplication'),(76,'Can view 帮派申请',19,'view_gangapplication'),(77,'Can add 核心技能',20,'add_skill'),(78,'Can change 核心技能',20,'change_skill'),(79,'Can delete 核心技能',20,'delete_skill'),(80,'Can view 核心技能',20,'view_skill'),(81,'Can add 玩家技能',21,'add_playerskill'),(82,'Can change 玩家技能',21,'change_playerskill'),(83,'Can delete 玩家技能',21,'delete_playerskill'),(84,'Can view 玩家技能',21,'view_playerskill'),(85,'Can add 游戏基础属性',22,'add_gamebase'),(86,'Can change 游戏基础属性',22,'change_gamebase'),(87,'Can delete 游戏基础属性',22,'delete_gamebase'),(88,'Can view 游戏基础属性',22,'view_gamebase'),(89,'Can add 技能等级',23,'add_skillranklevel'),(90,'Can change 技能等级',23,'change_skillranklevel'),(91,'Can delete 技能等级',23,'delete_skillranklevel'),(92,'Can view 技能等级',23,'view_skillranklevel'),(93,'Can add 队伍',24,'add_team'),(94,'Can change 队伍',24,'change_team'),(95,'Can delete 队伍',24,'delete_team'),(96,'Can view 队伍',24,'view_team'),(97,'Can add 队伍成员',25,'add_teammember'),(98,'Can change 队伍成员',25,'change_teammember'),(99,'Can delete 队伍成员',25,'delete_teammember'),(100,'Can view 队伍成员',25,'view_teammember'),(101,'Can add 游戏用户',26,'add_user'),(102,'Can change 游戏用户',26,'change_user'),(103,'Can delete 游戏用户',26,'delete_user'),(104,'Can view 游戏用户',26,'view_user'),(105,'Can add player item',27,'add_playeritem'),(106,'Can change player item',27,'change_playeritem'),(107,'Can delete player item',27,'delete_playeritem'),(108,'Can view player item',27,'view_playeritem'),(109,'Can add he cheng',28,'add_hecheng'),(110,'Can change he cheng',28,'change_hecheng'),(111,'Can delete he cheng',28,'delete_hecheng'),(112,'Can view he cheng',28,'view_hecheng'),(113,'Can add 地图物品实例',29,'add_gamemapitem'),(114,'Can change 地图物品实例',29,'change_gamemapitem'),(115,'Can delete 地图物品实例',29,'delete_gamemapitem'),(116,'Can view 地图物品实例',29,'view_gamemapitem'),(117,'Can add NPC实例',30,'add_gamemapnpc'),(118,'Can change NPC实例',30,'change_gamemapnpc'),(119,'Can delete NPC实例',30,'delete_gamemapnpc'),(120,'Can view NPC实例',30,'view_gamemapnpc'),(121,'Can add npc drop list',31,'add_npcdroplist'),(122,'Can change npc drop list',31,'change_npcdroplist'),(123,'Can delete npc drop list',31,'delete_npcdroplist'),(124,'Can view npc drop list',31,'view_npcdroplist'),(125,'Can add 玩家快捷键',32,'add_quickslot'),(126,'Can change 玩家快捷键',32,'change_quickslot'),(127,'Can delete 玩家快捷键',32,'delete_quickslot'),(128,'Can view 玩家快捷键',32,'view_quickslot'),(129,'Can add 玩家装备',33,'add_playerequipment'),(130,'Can change 玩家装备',33,'change_playerequipment'),(131,'Can delete 玩家装备',33,'delete_playerequipment'),(132,'Can view 玩家装备',33,'view_playerequipment');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$HUk4PO4EcbvXbqgZMU2FRf$L2zQE80AyGZfNEgFMckA2DP8ODbhCGEP0cdjsroDUII=','2025-06-18 17:09:23.466639',1,'admin','','','lzfdd937@163.com',1,1,'2025-06-10 12:11:15.636502');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2025-06-10 12:11:51.098581','1','斗破苍穹 (v0.1.0)',1,'[{\"added\": {}}]',22,1),(2,'2025-06-10 12:13:31.866286','1','斗破苍穹 (v0.1.0)',2,'[{\"changed\": {\"fields\": [\"\\u6e38\\u620f\\u4ecb\\u7ecd\"]}}]',22,1),(3,'2025-06-10 12:14:14.322041','1','斗破苍穹 (v0.1.0)',2,'[{\"changed\": {\"fields\": [\"\\u6e38\\u620f\\u4ecb\\u7ecd\"]}}]',22,1),(4,'2025-06-10 12:15:03.220781','1','斗破苍穹 (v0.1.0)',2,'[{\"changed\": {\"fields\": [\"\\u6e38\\u620f\\u4ecb\\u7ecd\"]}}]',22,1),(5,'2025-06-10 14:28:57.449088','1','乌坦城',1,'[{\"added\": {}}]',13,1),(6,'2025-06-10 14:29:16.183099','1','乌坦城 (乌坦城)',1,'[{\"added\": {}}]',7,1),(7,'2025-06-10 14:29:30.167910','1','加玛帝国',2,'[{\"changed\": {\"fields\": [\"Name\"]}}]',13,1),(8,'2025-06-10 14:29:48.924109','1','萧家大院',1,'[{\"added\": {}}]',12,1),(9,'2025-06-10 14:29:59.944768','1','斗破苍穹 (v0.1.0)',2,'[{\"changed\": {\"fields\": [\"\\u9ed8\\u8ba4\\u5730\\u56fe\\u5165\\u53e3\"]}}]',22,1),(10,'2025-06-13 05:39:37.294021','2','萧家后院',1,'[{\"added\": {}}]',12,1),(11,'2025-06-13 05:43:17.078151','1','GameNPC object (1)',1,'[{\"added\": {}}]',14,1),(12,'2025-06-13 05:52:09.076017','3','其他:聚气散',1,'[{\"added\": {}}]',15,1),(13,'2025-06-13 06:01:21.415477','3','药品:聚气散',2,'[{\"changed\": {\"fields\": [\"Category\"]}}]',15,1),(14,'2025-06-14 13:23:47.515809','4','GameMapNPC object (4)',1,'[{\"added\": {}}]',30,1),(15,'2025-06-14 14:38:24.997647','4','萧家后山',1,'[{\"added\": {}}]',12,1),(16,'2025-06-14 14:38:27.850034','1','萧家大院',2,'[{\"changed\": {\"fields\": [\"\\u4e1c\\u5411\\u8fde\\u63a5\"]}}]',12,1),(17,'2025-06-14 16:30:28.781737','2','美杜莎',1,'[{\"added\": {}}]',14,1),(18,'2025-06-14 16:30:38.117871','5','GameMapNPC object (5)',1,'[{\"added\": {}}]',30,1),(19,'2025-06-14 16:37:31.159984','1','GameMapItem object (1)',1,'[{\"added\": {}}]',29,1),(20,'2025-06-14 16:44:51.543758','1','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u6d88\\u5931\\u65f6\\u95f4\"]}}]',29,1),(21,'2025-06-15 03:20:29.538869','3','萧媚',1,'[{\"added\": {}}]',14,1),(22,'2025-06-15 03:29:56.998129','1','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u6d88\\u5931\\u65f6\\u95f4\"]}}]',29,1),(23,'2025-06-15 03:30:42.886247','6','map-4/npc-3',1,'[{\"added\": {}}]',30,1),(24,'2025-06-15 07:27:30.624315','7','map-1/npc-3',1,'[{\"added\": {}}]',30,1),(25,'2025-06-15 07:40:10.908581','1','萧战(ID:1)',2,'[{\"changed\": {\"fields\": [\"\\u5bf9\\u8bdd\\u6587\\u672c\"]}}]',14,1),(26,'2025-06-15 10:43:11.526152','1','普通攻击(黄阶初级)',1,'[{\"added\": {}}]',20,1),(27,'2025-06-15 10:43:31.194797','1','风火轮-普通攻击',1,'[{\"added\": {}}]',21,1),(28,'2025-06-15 15:10:05.423946','1','普通攻击',2,'[{\"changed\": {\"fields\": [\"\\u6700\\u5927\\u7ecf\\u9a8c\\u503c\"]}}]',21,1),(29,'2025-06-16 09:45:12.204691','5','map-1/npc-2',2,'[{\"changed\": {\"fields\": [\"\\u6570\\u91cf\"]}}]',30,1),(30,'2025-06-17 07:38:00.833187','1','玩家6的快捷键1',1,'[{\"added\": {}}]',32,1),(31,'2025-06-18 09:48:04.394155','1','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u62fe\\u53d6\\u8005\"]}}]',29,1),(32,'2025-06-18 12:04:18.581421','2','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u6d88\\u5931\\u65f6\\u95f4\"]}}]',29,1),(33,'2025-06-18 14:59:59.168510','2','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u6d88\\u5931\\u65f6\\u95f4\"]}}]',29,1),(34,'2025-06-18 15:29:43.381404','2','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u6d88\\u5931\\u65f6\\u95f4\"]}}]',29,1),(35,'2025-06-18 15:55:43.089538','2','聚气散',2,'[]',29,1),(36,'2025-06-18 15:56:16.783784','2','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u62fe\\u53d6\\u8005\"]}}]',29,1),(37,'2025-06-18 16:01:44.600411','2','聚气散',2,'[{\"changed\": {\"fields\": [\"\\u62fe\\u53d6\\u8005\"]}}]',29,1),(38,'2025-06-18 16:52:20.032161','5','装备:银月弯刀',1,'[{\"added\": {}}]',15,1),(39,'2025-06-18 16:54:01.325499','5','装备:银月弯刀',2,'[]',15,1),(40,'2025-06-18 16:54:21.212428','3','银月弯刀',1,'[{\"added\": {}}]',29,1),(41,'2025-06-18 17:09:26.917858','3','银月弯刀',2,'[]',29,1),(42,'2025-06-19 07:22:49.951535','6','装备:武士战甲',1,'[{\"added\": {}}]',15,1),(43,'2025-06-19 07:23:23.658453','6','武士战甲',1,'[{\"added\": {}}]',29,1),(44,'2025-06-19 09:18:59.156697','5','装备:银月弯刀',2,'[]',15,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(10,'game','chatmessage'),(22,'game','gamebase'),(7,'game','gamecity'),(11,'game','gameevent'),(12,'game','gamemap'),(13,'game','gamemaparea'),(29,'game','gamemapitem'),(30,'game','gamemapnpc'),(14,'game','gamenpc'),(8,'game','gamepage'),(9,'game','gang'),(19,'game','gangapplication'),(18,'game','gangmember'),(28,'game','hecheng'),(15,'game','item'),(31,'game','npcdroplist'),(16,'game','pagecomponent'),(17,'game','player'),(33,'game','playerequipment'),(27,'game','playeritem'),(21,'game','playerskill'),(32,'game','quickslot'),(20,'game','skill'),(23,'game','skillranklevel'),(24,'game','team'),(25,'game','teammember'),(26,'game','user'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-06-10 11:31:06.348535'),(2,'auth','0001_initial','2025-06-10 11:31:07.359458'),(3,'admin','0001_initial','2025-06-10 11:31:07.590957'),(4,'admin','0002_logentry_remove_auto_add','2025-06-10 11:31:07.597869'),(5,'admin','0003_logentry_add_action_flag_choices','2025-06-10 11:31:07.604487'),(6,'contenttypes','0002_remove_content_type_name','2025-06-10 11:31:07.751976'),(7,'auth','0002_alter_permission_name_max_length','2025-06-10 11:31:07.851699'),(8,'auth','0003_alter_user_email_max_length','2025-06-10 11:31:07.876503'),(9,'auth','0004_alter_user_username_opts','2025-06-10 11:31:07.885020'),(10,'auth','0005_alter_user_last_login_null','2025-06-10 11:31:07.956707'),(11,'auth','0006_require_contenttypes_0002','2025-06-10 11:31:07.963430'),(12,'auth','0007_alter_validators_add_error_messages','2025-06-10 11:31:07.970936'),(13,'auth','0008_alter_user_username_max_length','2025-06-10 11:31:08.054180'),(14,'auth','0009_alter_user_last_name_max_length','2025-06-10 11:31:08.146387'),(15,'auth','0010_alter_group_name_max_length','2025-06-10 11:31:08.169970'),(16,'auth','0011_update_proxy_permissions','2025-06-10 11:31:08.180807'),(17,'auth','0012_alter_user_first_name_max_length','2025-06-10 11:31:08.261130'),(18,'game','0001_initial','2025-06-10 11:31:12.890888'),(19,'sessions','0001_initial','2025-06-10 11:31:12.943404'),(20,'game','0002_player_gang_alter_gangmember_player','2025-06-11 10:49:57.849877'),(21,'game','0003_alter_item_options_alter_playeritem_options_and_more','2025-06-13 14:54:39.684459'),(22,'game','0004_player_last_active_and_more','2025-06-13 15:26:13.740630'),(23,'game','0005_remove_player_offline_at_player_is_online','2025-06-13 15:54:35.254397'),(24,'game','0006_gamemapnpc_is_boss_gamemapnpc_refresh_time','2025-06-14 06:06:53.626282'),(25,'game','0007_npcdroplist_and_more','2025-06-14 07:29:32.840044'),(26,'game','0008_remove_gamemapitem_game_gamema_map_id_877c0c_idx_and_more','2025-06-14 12:54:53.173773'),(27,'game','0009_alter_skillranklevel_unique_together_and_more','2025-06-15 15:08:38.986051'),(28,'game','0010_quickslot','2025-06-16 17:45:53.183912'),(29,'game','0002_playeritem_category_and_more','2025-06-18 10:17:47.554564'),(30,'game','0003_rename_game_invent_player__32bba0_idx_game_player_player__3c5c5c_idx_and_more','2025-06-18 10:30:38.670235'),(31,'game','0002_remove_playeritem_equipment_post','2025-06-19 08:06:59.503052'),(32,'game','0003_playeritem_equipment_post','2025-06-19 08:06:59.593930'),(33,'game','0004_playeritem_max_naijiu_alter_playeritem_naijiu','2025-06-19 10:04:12.028223');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_chatmessage`
--

DROP TABLE IF EXISTS `game_chatmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_chatmessage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type_id` smallint unsigned NOT NULL,
  `sender` smallint unsigned DEFAULT NULL,
  `sender_name` varchar(50) DEFAULT NULL,
  `message` varchar(256) DEFAULT NULL,
  `receiver` smallint unsigned DEFAULT NULL,
  `bangpai_id` smallint unsigned DEFAULT NULL,
  `duiwu_id` smallint unsigned DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_chatmessage_type_id_23f7de2d` (`type_id`),
  KEY `game_chatmessage_sender_9a11754a` (`sender`),
  KEY `game_chatmessage_receiver_f7375a2d` (`receiver`),
  KEY `game_chatmessage_bangpai_id_139c341c` (`bangpai_id`),
  KEY `game_chatmessage_duiwu_id_723404f6` (`duiwu_id`),
  KEY `game_chatmessage_created_at_a9d4a106` (`created_at`),
  KEY `game_chatme_type_id_02ed22_idx` (`type_id`,`created_at` DESC),
  KEY `game_chatme_bangpai_a8f917_idx` (`bangpai_id`,`created_at` DESC),
  KEY `game_chatme_sender_78e900_idx` (`sender`,`receiver`,`created_at` DESC),
  CONSTRAINT `game_chatmessage_chk_1` CHECK ((`type_id` >= 0)),
  CONSTRAINT `game_chatmessage_chk_2` CHECK ((`sender` >= 0)),
  CONSTRAINT `game_chatmessage_chk_3` CHECK ((`receiver` >= 0)),
  CONSTRAINT `game_chatmessage_chk_4` CHECK ((`bangpai_id` >= 0)),
  CONSTRAINT `game_chatmessage_chk_5` CHECK ((`duiwu_id` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_chatmessage`
--

LOCK TABLES `game_chatmessage` WRITE;
/*!40000 ALTER TABLE `game_chatmessage` DISABLE KEYS */;
INSERT INTO `game_chatmessage` VALUES (2,1,3,'我叫安生啊',' 欢迎 <a href=\"/wap/?cmd={}\">{}</a> 加入游戏！',NULL,NULL,NULL,'2025-06-10 14:52:14.569670'),(3,1,4,'啊啊啊啊',' 欢迎 <a href=\"/wap/?cmd={}\">{}</a> 加入游戏！',NULL,NULL,NULL,'2025-06-10 15:10:50.529576'),(4,2,1001,'江湖大侠','啊啊啊啊',NULL,NULL,NULL,'2025-06-10 19:07:11.298305'),(5,2,1001,'江湖大侠','干什么',NULL,NULL,NULL,'2025-06-10 19:22:17.822810'),(6,2,4,'啊啊啊啊','啊啊啊啊啊',NULL,NULL,NULL,'2025-06-11 02:56:00.108610'),(7,2,3,'我叫安生啊','你好',NULL,NULL,NULL,'2025-06-11 02:56:53.602518'),(8,2,3,'我叫安生啊','你好',NULL,NULL,NULL,'2025-06-11 02:57:58.137242'),(9,2,3,'我叫安生啊','什么',NULL,NULL,NULL,'2025-06-11 02:58:10.612707'),(10,2,3,'我叫安生啊','今天是星期三',NULL,NULL,NULL,'2025-06-11 02:58:18.492880'),(11,2,4,'啊啊啊啊','你好',NULL,NULL,NULL,'2025-06-11 03:43:11.994682'),(12,2,4,'啊啊啊啊','刚睡醒，好困',NULL,NULL,NULL,'2025-06-11 07:13:09.423116'),(13,2,4,'啊啊啊啊','不知道干啥好',NULL,NULL,NULL,'2025-06-11 07:13:21.895283'),(14,2,3,'我叫安生啊','那就睡觉',NULL,NULL,NULL,'2025-06-11 07:14:03.602385'),(15,1,NULL,'幸运阁',' 一个新的宗门势力【幸运阁】诞生了！',NULL,NULL,NULL,'2025-06-11 10:15:30.754688'),(16,1,NULL,'幸运阁1',' 一个新的宗门势力-【幸运阁1】诞生了！',NULL,NULL,NULL,'2025-06-11 10:30:43.019100'),(17,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',NULL,NULL,NULL,'2025-06-11 16:47:44.095227'),(18,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-11 16:52:44.475535'),(21,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-12 10:58:24.368600'),(22,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-12 13:09:18.478250'),(23,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-12 15:29:27.059956'),(24,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-12 15:35:39.625599'),(25,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-12 15:37:03.395000'),(26,4,NULL,NULL,'<a href=\"/wap/?cmd={}\">欢迎 {} 加入本宗门~</a>',NULL,2,NULL,'2025-06-12 17:18:50.506013'),(27,4,NULL,NULL,'<a href=\"/wap/?cmd={}\">欢迎 {} 加入本宗门~</a>',NULL,2,NULL,'2025-06-12 17:19:26.659761'),(28,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-13 02:58:30.077332'),(29,4,NULL,NULL,'<a href=\"/wap/?cmd={}\">欢迎 {} 加入本宗门~</a>',NULL,2,NULL,'2025-06-13 04:45:14.387053'),(30,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-13 04:48:25.252969'),(31,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-13 04:57:43.481408'),(32,4,NULL,NULL,'宗门<a href=\"/wap/?cmd={}\">{}</a>拒绝了你的加入申请',6,NULL,NULL,'2025-06-13 04:58:08.871892'),(33,3,NULL,NULL,'有人申请加入你的宗门啦，快去宗门页面看看是谁吧~',3,NULL,NULL,'2025-06-13 05:02:55.420535'),(34,3,NULL,NULL,'宗门<a href=\"/wap/?cmd={}\">{}</a>同意了你的加入申请',6,NULL,NULL,'2025-06-13 05:03:05.476788'),(35,4,NULL,NULL,'<a href=\"/wap/?cmd={}\">欢迎 {} 加入本宗门~</a>',NULL,2,NULL,'2025-06-13 05:03:05.476830'),(36,2,3,'我叫安生啊','服了',NULL,NULL,NULL,'2025-06-13 16:02:48.154923'),(37,2,6,'风火轮','方向错了，事倍功半',NULL,NULL,NULL,'2025-06-15 07:09:37.120756');
/*!40000 ALTER TABLE `game_chatmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamebase`
--

DROP TABLE IF EXISTS `game_gamebase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamebase` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext,
  `status` varchar(20) NOT NULL,
  `version` varchar(20) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `huobi` varchar(50) NOT NULL,
  `config_params` json NOT NULL,
  `default_map_id` bigint DEFAULT NULL,
  `default_skill_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamebase_default_map_id_ab28f1b6_fk_game_gamemap_id` (`default_map_id`),
  KEY `game_gamebase_default_skill_id_33e5d251_fk_game_skill_id` (`default_skill_id`),
  CONSTRAINT `game_gamebase_default_map_id_ab28f1b6_fk_game_gamemap_id` FOREIGN KEY (`default_map_id`) REFERENCES `game_gamemap` (`id`),
  CONSTRAINT `game_gamebase_default_skill_id_33e5d251_fk_game_skill_id` FOREIGN KEY (`default_skill_id`) REFERENCES `game_skill` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamebase`
--

LOCK TABLES `game_gamebase` WRITE;
/*!40000 ALTER TABLE `game_gamebase` DISABLE KEYS */;
INSERT INTO `game_gamebase` VALUES (1,'斗破苍穹','这里是属于斗气的世界。没有花俏艳丽的魔法，有的，仅仅是繁衍到巅峰的斗气！<br>\r\n三十年河东，三十年河西，莫欺少年穷！ <br>\r\n收异火，寻宝物，炼丹药，斗魂族。一步步走向斗气大陆巅峰吧！<br>','kfz','0.1.0','2025-06-10 12:11:51.094849','金币','{}',1,NULL);
/*!40000 ALTER TABLE `game_gamebase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamecity`
--

DROP TABLE IF EXISTS `game_gamecity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamecity` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext,
  `area_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamecity_area_id_8463866f_fk_game_gamemaparea_id` (`area_id`),
  CONSTRAINT `game_gamecity_area_id_8463866f_fk_game_gamemaparea_id` FOREIGN KEY (`area_id`) REFERENCES `game_gamemaparea` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamecity`
--

LOCK TABLES `game_gamecity` WRITE;
/*!40000 ALTER TABLE `game_gamecity` DISABLE KEYS */;
INSERT INTO `game_gamecity` VALUES (1,'乌坦城','',1);
/*!40000 ALTER TABLE `game_gamecity` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gameevent`
--

DROP TABLE IF EXISTS `game_gameevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gameevent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(20) DEFAULT NULL,
  `function_name` varchar(50) DEFAULT NULL,
  `function_params` json DEFAULT NULL,
  `state_machine_config` json DEFAULT NULL,
  `success_message` longtext NOT NULL,
  `failure_message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `game_gameev_categor_1cc7d6_idx` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gameevent`
--

LOCK TABLES `game_gameevent` WRITE;
/*!40000 ALTER TABLE `game_gameevent` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_gameevent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamemap`
--

DROP TABLE IF EXISTS `game_gamemap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamemap` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `desc` longtext NOT NULL,
  `is_city` tinyint(1) NOT NULL,
  `is_safe_zone` tinyint(1) NOT NULL,
  `refresh_time` int NOT NULL,
  `params` json NOT NULL,
  `city_id` bigint DEFAULT NULL,
  `east_id` bigint DEFAULT NULL,
  `north_id` bigint DEFAULT NULL,
  `south_id` bigint DEFAULT NULL,
  `west_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamema_is_safe_585ff5_idx` (`is_safe_zone`),
  KEY `game_gamema_is_city_6af311_idx` (`is_city`),
  KEY `game_gamemap_city_id_a256e042_fk_game_gamecity_id` (`city_id`),
  KEY `game_gamemap_east_id_32727a74_fk_game_gamemap_id` (`east_id`),
  KEY `game_gamemap_north_id_c193cf1f_fk_game_gamemap_id` (`north_id`),
  KEY `game_gamemap_south_id_ec283572_fk_game_gamemap_id` (`south_id`),
  KEY `game_gamemap_west_id_19f8fbc7_fk_game_gamemap_id` (`west_id`),
  CONSTRAINT `game_gamemap_city_id_a256e042_fk_game_gamecity_id` FOREIGN KEY (`city_id`) REFERENCES `game_gamecity` (`id`),
  CONSTRAINT `game_gamemap_east_id_32727a74_fk_game_gamemap_id` FOREIGN KEY (`east_id`) REFERENCES `game_gamemap` (`id`),
  CONSTRAINT `game_gamemap_north_id_c193cf1f_fk_game_gamemap_id` FOREIGN KEY (`north_id`) REFERENCES `game_gamemap` (`id`),
  CONSTRAINT `game_gamemap_south_id_ec283572_fk_game_gamemap_id` FOREIGN KEY (`south_id`) REFERENCES `game_gamemap` (`id`),
  CONSTRAINT `game_gamemap_west_id_19f8fbc7_fk_game_gamemap_id` FOREIGN KEY (`west_id`) REFERENCES `game_gamemap` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamemap`
--

LOCK TABLES `game_gamemap` WRITE;
/*!40000 ALTER TABLE `game_gamemap` DISABLE KEYS */;
INSERT INTO `game_gamemap` VALUES (1,'萧家大院','',0,0,300,'{}',1,4,2,NULL,NULL),(2,'萧家后院','',0,0,300,'{}',1,NULL,NULL,1,NULL),(4,'萧家后山','',0,0,300,'{}',1,NULL,NULL,NULL,1);
/*!40000 ALTER TABLE `game_gamemap` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamemaparea`
--

DROP TABLE IF EXISTS `game_gamemaparea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamemaparea` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext,
  `area_type` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamema_area_ty_9e5e39_idx` (`area_type`),
  CONSTRAINT `game_gamemaparea_chk_1` CHECK ((`area_type` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamemaparea`
--

LOCK TABLES `game_gamemaparea` WRITE;
/*!40000 ALTER TABLE `game_gamemaparea` DISABLE KEYS */;
INSERT INTO `game_gamemaparea` VALUES (1,'加玛帝国','',0);
/*!40000 ALTER TABLE `game_gamemaparea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamemapitem`
--

DROP TABLE IF EXISTS `game_gamemapitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamemapitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `count` int NOT NULL,
  `expire_time` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `item_id` bigint NOT NULL,
  `map_id` int unsigned DEFAULT NULL,
  `picked_by` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamemapitem_item_id_b3ddb03c_fk_game_items_id` (`item_id`),
  KEY `game_gamema_expire__d1b446_idx` (`expire_time`),
  KEY `game_gamema_map_id_877c0c_idx` (`map_id`),
  KEY `game_gamemapitem_map_id_7bd3e6e5` (`map_id`),
  CONSTRAINT `game_gamemapitem_item_id_b3ddb03c_fk_game_items_id` FOREIGN KEY (`item_id`) REFERENCES `game_items` (`id`),
  CONSTRAINT `game_gamemapitem_chk_1` CHECK ((`map_id` >= 0)),
  CONSTRAINT `game_gamemapitem_chk_2` CHECK ((`picked_by` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamemapitem`
--

LOCK TABLES `game_gamemapitem` WRITE;
/*!40000 ALTER TABLE `game_gamemapitem` DISABLE KEYS */;
INSERT INTO `game_gamemapitem` VALUES (1,1,'2025-06-29 22:00:00.000000','2025-06-14 16:37:31.156547',3,1,6),(3,1,'2025-06-19 16:54:20.000000','2025-06-18 16:54:21.209648',5,1,3),(4,1,'2025-06-20 17:06:02.000000','2025-06-18 16:56:02.871928',5,1,6),(5,1,'2025-06-18 17:21:27.759870','2025-06-18 17:11:27.760079',5,1,3),(6,2,'2025-06-20 07:23:22.000000','2025-06-19 07:23:23.655430',6,2,3),(7,1,'2025-06-19 08:51:17.327055','2025-06-19 08:41:17.327373',6,2,3),(8,1,'2025-06-19 10:12:05.996851','2025-06-19 10:02:05.997193',5,1,3),(9,1,'2025-06-19 10:16:48.705889','2025-06-19 10:06:48.706049',6,1,3);
/*!40000 ALTER TABLE `game_gamemapitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamemapnpc`
--

DROP TABLE IF EXISTS `game_gamemapnpc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamemapnpc` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `count` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `map_id` int unsigned DEFAULT NULL,
  `npc_id` int unsigned NOT NULL,
  `next_refresh_time` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamema_created_5ef20e_idx` (`created_at`),
  KEY `game_gamema_map_id_a35f8c_idx` (`map_id`),
  KEY `game_gamemapnpc_map_id_4c49cda4` (`map_id`),
  KEY `game_gamemapnpc_npc_id_4f06b363` (`npc_id`),
  CONSTRAINT `game_gamemapnpc_chk_1` CHECK ((`map_id` >= 0)),
  CONSTRAINT `game_gamemapnpc_chk_2` CHECK ((`npc_id` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamemapnpc`
--

LOCK TABLES `game_gamemapnpc` WRITE;
/*!40000 ALTER TABLE `game_gamemapnpc` DISABLE KEYS */;
INSERT INTO `game_gamemapnpc` VALUES (4,1,'2025-06-14 13:23:47.512706',1,1,3600),(5,2,'2025-06-14 16:30:38.108651',1,2,3600),(6,1,'2025-06-15 03:30:42.882488',4,3,3600),(7,1,'2025-06-15 07:27:30.620845',1,3,3600);
/*!40000 ALTER TABLE `game_gamemapnpc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamenpc`
--

DROP TABLE IF EXISTS `game_gamenpc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamenpc` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `npc_type` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `level` int NOT NULL,
  `hp` int DEFAULT NULL,
  `attack` int DEFAULT NULL,
  `defense` int DEFAULT NULL,
  `exp_reward` int NOT NULL,
  `gold_reward` int NOT NULL,
  `drop_items` json DEFAULT NULL,
  `dialogue` longtext,
  `shop_items` json DEFAULT NULL,
  `show_conditions` json NOT NULL,
  `is_boss` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gamenp_npc_typ_4c29e5_idx` (`npc_type`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamenpc`
--

LOCK TABLES `game_gamenpc` WRITE;
/*!40000 ALTER TABLE `game_gamenpc` DISABLE KEYS */;
INSERT INTO `game_gamenpc` VALUES (1,'npc','萧战','萧炎父亲',1,NULL,NULL,NULL,0,0,NULL,'有什么事吗？',NULL,'{}',0),(2,'monster','美杜莎','天啊太吓人了',1,100,10,2,10,0,NULL,'',NULL,'{}',0),(3,'npc','萧媚','萧炎他大表姐',1,NULL,NULL,NULL,0,0,NULL,'',NULL,'{}',0);
/*!40000 ALTER TABLE `game_gamenpc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gamepage`
--

DROP TABLE IF EXISTS `game_gamepage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gamepage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `custom_css` longtext NOT NULL,
  `custom_js` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gamepage`
--

LOCK TABLES `game_gamepage` WRITE;
/*!40000 ALTER TABLE `game_gamepage` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_gamepage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gang`
--

DROP TABLE IF EXISTS `game_gang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gang` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` longtext NOT NULL,
  `reputation` int unsigned NOT NULL,
  `money` int unsigned NOT NULL,
  `level` int unsigned NOT NULL,
  `max_count` int unsigned NOT NULL,
  `max_exp` int unsigned NOT NULL,
  `exp` int unsigned NOT NULL,
  `location` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `params` json NOT NULL,
  `icon` varchar(200) DEFAULT NULL,
  `leader_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `game_gang_leader_id_52e7e417_fk_game_player_id` (`leader_id`),
  CONSTRAINT `game_gang_leader_id_52e7e417_fk_game_player_id` FOREIGN KEY (`leader_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_gang_chk_1` CHECK ((`reputation` >= 0)),
  CONSTRAINT `game_gang_chk_2` CHECK ((`money` >= 0)),
  CONSTRAINT `game_gang_chk_3` CHECK ((`level` >= 0)),
  CONSTRAINT `game_gang_chk_4` CHECK ((`max_count` >= 0)),
  CONSTRAINT `game_gang_chk_5` CHECK ((`max_exp` >= 0)),
  CONSTRAINT `game_gang_chk_6` CHECK ((`exp` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gang`
--

LOCK TABLES `game_gang` WRITE;
/*!40000 ALTER TABLE `game_gang` DISABLE KEYS */;
INSERT INTO `game_gang` VALUES (2,'幸运阁1','',0,1000,1,3,10000,0,'','2025-06-11 10:30:43.004629','{}',NULL,3);
/*!40000 ALTER TABLE `game_gang` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gangapplication`
--

DROP TABLE IF EXISTS `game_gangapplication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gangapplication` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `applied_time` datetime(6) NOT NULL,
  `status` varchar(20) NOT NULL,
  `gang_id` bigint NOT NULL,
  `player_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_gangapplication_gang_id_5b47162c_fk_game_gang_id` (`gang_id`),
  KEY `game_gangapplication_player_id_2bf394a1_fk_game_player_id` (`player_id`),
  CONSTRAINT `game_gangapplication_gang_id_5b47162c_fk_game_gang_id` FOREIGN KEY (`gang_id`) REFERENCES `game_gang` (`id`),
  CONSTRAINT `game_gangapplication_player_id_2bf394a1_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gangapplication`
--

LOCK TABLES `game_gangapplication` WRITE;
/*!40000 ALTER TABLE `game_gangapplication` DISABLE KEYS */;
INSERT INTO `game_gangapplication` VALUES (3,'2025-06-11 16:52:44.469776','accepted',2,4),(4,'2025-06-12 10:58:24.359980','reject',2,3),(8,'2025-06-12 15:37:03.388955','accepted',2,6),(9,'2025-06-13 02:58:30.068778','accepted',2,6),(10,'2025-06-13 04:48:25.244264','reject',2,6),(11,'2025-06-13 04:57:43.474598','rejected',2,6),(12,'2025-06-13 05:02:55.410971','accepted',2,6);
/*!40000 ALTER TABLE `game_gangapplication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_gangmember`
--

DROP TABLE IF EXISTS `game_gangmember`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_gangmember` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `join_date` datetime(6) NOT NULL,
  `position` varchar(20) NOT NULL,
  `contribution` int unsigned NOT NULL,
  `gang_id` bigint NOT NULL,
  `player_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `game_gangmember_player_id_gang_id_046f69b8_uniq` (`player_id`,`gang_id`),
  KEY `game_gangmember_gang_id_6b390080_fk_game_gang_id` (`gang_id`),
  CONSTRAINT `game_gangmember_gang_id_6b390080_fk_game_gang_id` FOREIGN KEY (`gang_id`) REFERENCES `game_gang` (`id`),
  CONSTRAINT `game_gangmember_player_id_b7b7411a_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_gangmember_chk_1` CHECK ((`contribution` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_gangmember`
--

LOCK TABLES `game_gangmember` WRITE;
/*!40000 ALTER TABLE `game_gangmember` DISABLE KEYS */;
INSERT INTO `game_gangmember` VALUES (1,'2025-06-11 10:30:43.012068','bz',0,2,3),(2,'2025-06-12 17:16:14.811891','cy',0,2,4),(6,'2025-06-13 05:03:05.462152','cy',0,2,6);
/*!40000 ALTER TABLE `game_gangmember` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_hecheng`
--

DROP TABLE IF EXISTS `game_hecheng`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_hecheng` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `required_materials` json NOT NULL,
  `success_rate` smallint unsigned NOT NULL,
  `item_id` bigint DEFAULT NULL,
  `result_item_id` bigint NOT NULL,
  `forger_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`),
  KEY `game_hecheng_result_item_id_90d22c89_fk_game_items_id` (`result_item_id`),
  KEY `game_hecheng_forger_id_00b672ec_fk_game_user_id` (`forger_id`),
  CONSTRAINT `game_hecheng_forger_id_00b672ec_fk_game_user_id` FOREIGN KEY (`forger_id`) REFERENCES `game_user` (`id`),
  CONSTRAINT `game_hecheng_item_id_0a2edb1f_fk_game_items_id` FOREIGN KEY (`item_id`) REFERENCES `game_items` (`id`),
  CONSTRAINT `game_hecheng_result_item_id_90d22c89_fk_game_items_id` FOREIGN KEY (`result_item_id`) REFERENCES `game_items` (`id`),
  CONSTRAINT `game_hecheng_chk_1` CHECK ((`success_rate` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_hecheng`
--

LOCK TABLES `game_hecheng` WRITE;
/*!40000 ALTER TABLE `game_hecheng` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_hecheng` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_items`
--

DROP TABLE IF EXISTS `game_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` longtext,
  `category` varchar(20) NOT NULL,
  `level` int NOT NULL,
  `weight` int NOT NULL,
  `price` int NOT NULL,
  `jiaoyi` tinyint(1) NOT NULL,
  `zengsong` tinyint(1) NOT NULL,
  `attack` int NOT NULL,
  `defense` int NOT NULL,
  `minjie` int NOT NULL,
  `linghunli` int NOT NULL,
  `hp` int NOT NULL,
  `set_id` int NOT NULL,
  `set_bonus` json NOT NULL,
  `rank` int NOT NULL,
  `max_naijiu` int DEFAULT NULL,
  `attrs` json NOT NULL,
  `duidie` tinyint(1) NOT NULL,
  `equipment_post` smallint unsigned DEFAULT NULL,
  `is_kaikong` tinyint(1) NOT NULL,
  `max_kaikong` int DEFAULT NULL,
  `max_qianghua` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_items_name_1095d308` (`name`),
  KEY `game_items_category_d6bba090` (`category`),
  KEY `game_items_set_id_e8ebedd2` (`set_id`),
  KEY `game_items_rank_64531266` (`rank`),
  KEY `game_items_categor_d86b1f_idx` (`category`),
  CONSTRAINT `game_items_chk_1` CHECK ((`equipment_post` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_items`
--

LOCK TABLES `game_items` WRITE;
/*!40000 ALTER TABLE `game_items` DISABLE KEYS */;
INSERT INTO `game_items` VALUES (3,'聚气散','斗之气升级斗者时，成功率100%','2',1,1,100,1,1,0,0,0,0,0,0,'{}',1,100,'{}',1,1,0,0,10),(5,'银月弯刀','','1',1,1,100,1,1,100,20,5,0,0,0,'{}',1,0,'{}',0,1,0,0,10),(6,'武士战甲','','1',1,1,100,1,1,2,10,0,0,0,0,'{}',1,0,'{}',0,3,0,0,10);
/*!40000 ALTER TABLE `game_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_npcdroplist`
--

DROP TABLE IF EXISTS `game_npcdroplist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_npcdroplist` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `gailv` int NOT NULL,
  `item_id` bigint NOT NULL,
  `npc_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_npcdroplist_item_id_1dc30494_fk_game_items_id` (`item_id`),
  KEY `game_npcdroplist_npc_id_e6be56ad_fk_game_gamenpc_id` (`npc_id`),
  CONSTRAINT `game_npcdroplist_item_id_1dc30494_fk_game_items_id` FOREIGN KEY (`item_id`) REFERENCES `game_items` (`id`),
  CONSTRAINT `game_npcdroplist_npc_id_e6be56ad_fk_game_gamenpc_id` FOREIGN KEY (`npc_id`) REFERENCES `game_gamenpc` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_npcdroplist`
--

LOCK TABLES `game_npcdroplist` WRITE;
/*!40000 ALTER TABLE `game_npcdroplist` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_npcdroplist` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_pagecomponent`
--

DROP TABLE IF EXISTS `game_pagecomponent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_pagecomponent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `display_text` longtext NOT NULL,
  `show_condition` longtext NOT NULL,
  `position` int unsigned NOT NULL,
  `component_type` varchar(128) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `event_id` bigint DEFAULT NULL,
  `page_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_pageco_page_id_408228_idx` (`page_id`),
  KEY `game_pageco_event_i_51aa98_idx` (`event_id`),
  CONSTRAINT `game_pagecomponent_event_id_492a29e4_fk_game_gameevent_id` FOREIGN KEY (`event_id`) REFERENCES `game_gameevent` (`id`),
  CONSTRAINT `game_pagecomponent_page_id_7ae74c81_fk_game_gamepage_id` FOREIGN KEY (`page_id`) REFERENCES `game_gamepage` (`id`),
  CONSTRAINT `game_pagecomponent_chk_1` CHECK ((`position` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_pagecomponent`
--

LOCK TABLES `game_pagecomponent` WRITE;
/*!40000 ALTER TABLE `game_pagecomponent` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_pagecomponent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_player`
--

DROP TABLE IF EXISTS `game_player`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_player` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `avatar` varchar(200) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `gender` varchar(1) NOT NULL,
  `signature` varchar(100) NOT NULL,
  `level` int unsigned NOT NULL,
  `current_exp` bigint unsigned NOT NULL,
  `current_hp` int unsigned NOT NULL,
  `max_hp` int unsigned NOT NULL,
  `min_attack` int unsigned NOT NULL,
  `max_attack` int unsigned NOT NULL,
  `min_defense` int unsigned NOT NULL,
  `max_defense` int unsigned NOT NULL,
  `agility` int unsigned NOT NULL,
  `linghunli` int unsigned NOT NULL,
  `reputation` int NOT NULL,
  `params` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `map_id` bigint DEFAULT NULL,
  `marriage_id` bigint DEFAULT NULL,
  `user_id` bigint DEFAULT NULL,
  `gang_id` bigint DEFAULT NULL,
  `last_active` datetime(6) NOT NULL,
  `is_online` tinyint(1) NOT NULL,
  `bag_capacity` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `marriage_id` (`marriage_id`),
  KEY `game_player_user_id_94446fa4_fk_game_user_id` (`user_id`),
  KEY `game_player_name_13b648_idx` (`name`),
  KEY `game_player_level_86a0f4_idx` (`level`),
  KEY `game_player_map_id_c1128b7b_fk_game_gamemap_id` (`map_id`),
  KEY `game_player_gang_id_0cce0085_fk_game_gang_id` (`gang_id`),
  KEY `game_player_last_ac_a4203a_idx` (`last_active`),
  CONSTRAINT `game_player_gang_id_0cce0085_fk_game_gang_id` FOREIGN KEY (`gang_id`) REFERENCES `game_gang` (`id`),
  CONSTRAINT `game_player_map_id_c1128b7b_fk_game_gamemap_id` FOREIGN KEY (`map_id`) REFERENCES `game_gamemap` (`id`),
  CONSTRAINT `game_player_marriage_id_c622b210_fk_game_player_id` FOREIGN KEY (`marriage_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_player_user_id_94446fa4_fk_game_user_id` FOREIGN KEY (`user_id`) REFERENCES `game_user` (`id`),
  CONSTRAINT `game_player_chk_1` CHECK ((`level` >= 0)),
  CONSTRAINT `game_player_chk_10` CHECK ((`linghunli` >= 0)),
  CONSTRAINT `game_player_chk_2` CHECK ((`current_exp` >= 0)),
  CONSTRAINT `game_player_chk_3` CHECK ((`current_hp` >= 0)),
  CONSTRAINT `game_player_chk_4` CHECK ((`max_hp` >= 0)),
  CONSTRAINT `game_player_chk_5` CHECK ((`min_attack` >= 0)),
  CONSTRAINT `game_player_chk_6` CHECK ((`max_attack` >= 0)),
  CONSTRAINT `game_player_chk_7` CHECK ((`min_defense` >= 0)),
  CONSTRAINT `game_player_chk_8` CHECK ((`max_defense` >= 0)),
  CONSTRAINT `game_player_chk_9` CHECK ((`agility` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_player`
--

LOCK TABLES `game_player` WRITE;
/*!40000 ALTER TABLE `game_player` DISABLE KEYS */;
INSERT INTO `game_player` VALUES (3,NULL,'我叫安生啊','M','',1,0,100,100,10,20,5,10,10,0,0,'{}','2025-06-10 14:52:14.565346',1,NULL,1,2,'2025-06-18 15:17:53.936361',1,100),(4,NULL,'啊啊啊啊','F','',1,0,100,100,10,20,5,10,10,0,0,'{}','2025-06-10 15:10:50.516576',1,NULL,2,NULL,'2025-06-13 15:26:13.497601',0,100),(6,NULL,'风火轮','M','杀啊啊啊啊啊啊啊啊啊',1,0,100,100,10,20,5,10,10,0,0,'{}','2025-06-11 17:14:46.855310',1,NULL,6,NULL,'2025-06-18 15:16:57.521170',1,100);
/*!40000 ALTER TABLE `game_player` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_player_equipment`
--

DROP TABLE IF EXISTS `game_player_equipment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_player_equipment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `position` smallint unsigned NOT NULL,
  `hp` int NOT NULL,
  `attack` int NOT NULL,
  `defense` int NOT NULL,
  `minjie` int NOT NULL,
  `linghunli` int NOT NULL,
  `player_id` bigint NOT NULL,
  `item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `game_player_equipment_player_id_position_2274867c_uniq` (`player_id`,`position`),
  KEY `game_player_player__c06b28_idx` (`player_id`,`position`),
  KEY `game_player_equipment_item_id_4457e33f_fk_game_inventory_id` (`item_id`),
  KEY `game_player_equipment_position_d64cab4c` (`position`),
  CONSTRAINT `game_player_equipment_item_id_4457e33f_fk_game_inventory_id` FOREIGN KEY (`item_id`) REFERENCES `game_player_item` (`id`),
  CONSTRAINT `game_player_equipment_player_id_2913eb2f_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_player_equipment_chk_1` CHECK ((`position` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_player_equipment`
--

LOCK TABLES `game_player_equipment` WRITE;
/*!40000 ALTER TABLE `game_player_equipment` DISABLE KEYS */;
INSERT INTO `game_player_equipment` VALUES (16,1,0,0,0,0,0,3,9);
/*!40000 ALTER TABLE `game_player_equipment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_player_item`
--

DROP TABLE IF EXISTS `game_player_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_player_item` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `count` int NOT NULL,
  `is_bound` tinyint(1) NOT NULL,
  `baoshi` json NOT NULL,
  `is_equipped` tinyint(1) NOT NULL,
  `naijiu` int DEFAULT NULL,
  `qianghua_level` int NOT NULL,
  `attrs` json NOT NULL,
  `expiration_time` datetime(6) DEFAULT NULL,
  `item_id` bigint NOT NULL,
  `attack` int NOT NULL,
  `defense` int NOT NULL,
  `hp` int NOT NULL,
  `kaikong_count` int DEFAULT NULL,
  `linghunli` int NOT NULL,
  `minjie` int NOT NULL,
  `player_id` bigint NOT NULL,
  `category` smallint unsigned NOT NULL,
  `equipment_post` smallint unsigned DEFAULT NULL,
  `max_naijiu` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_inventory_item_id_c9e7b780_fk_game_items_id` (`item_id`),
  KEY `game_inventory_player_id_91dc8bb8_fk_game_player_id` (`player_id`),
  KEY `game_invent_player__5ab692_idx` (`player_id`,`category`),
  KEY `game_inventory_category_95faaa81` (`category`),
  KEY `game_player_equipped_idx` (`player_id`,`is_equipped`),
  CONSTRAINT `game_inventory_item_id_c9e7b780_fk_game_items_id` FOREIGN KEY (`item_id`) REFERENCES `game_items` (`id`),
  CONSTRAINT `game_inventory_player_id_91dc8bb8_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_player_item_chk_1` CHECK ((`category` >= 0)),
  CONSTRAINT `game_player_item_chk_2` CHECK ((`equipment_post` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_player_item`
--

LOCK TABLES `game_player_item` WRITE;
/*!40000 ALTER TABLE `game_player_item` DISABLE KEYS */;
INSERT INTO `game_player_item` VALUES (2,12,0,'[]',0,NULL,0,'{}',NULL,3,0,0,0,0,0,0,6,3,NULL,100),(3,1,0,'[]',0,NULL,0,'{}',NULL,3,0,0,0,0,0,0,3,2,1,100),(9,1,0,'[]',1,0,0,'{}',NULL,5,100,20,0,0,0,5,3,1,1,0),(10,1,0,'[]',0,0,0,'{}',NULL,6,2,10,0,0,0,0,3,1,3,0);
/*!40000 ALTER TABLE `game_player_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_playerskill`
--

DROP TABLE IF EXISTS `game_playerskill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_playerskill` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `current_level` smallint unsigned NOT NULL,
  `current_xp` int unsigned NOT NULL,
  `player_id` bigint NOT NULL,
  `skill_id` bigint NOT NULL,
  `attack` smallint NOT NULL,
  `defense` smallint NOT NULL,
  `douqi` smallint NOT NULL,
  `linghunli` smallint NOT NULL,
  `max_xp` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_playerskill_skill_id_5e463e14_fk_game_skill_id` (`skill_id`),
  KEY `game_playerskill_player_id_22de0c7d` (`player_id`),
  KEY `game_player_player__07076a_idx` (`player_id`,`current_level`),
  KEY `game_player_attack_beae48_idx` (`attack`,`defense`),
  CONSTRAINT `game_playerskill_player_id_22de0c7d_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_playerskill_skill_id_5e463e14_fk_game_skill_id` FOREIGN KEY (`skill_id`) REFERENCES `game_skill` (`id`),
  CONSTRAINT `game_playerskill_chk_1` CHECK ((`current_level` >= 0)),
  CONSTRAINT `game_playerskill_chk_2` CHECK ((`current_xp` >= 0)),
  CONSTRAINT `game_playerskill_chk_3` CHECK ((`max_xp` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_playerskill`
--

LOCK TABLES `game_playerskill` WRITE;
/*!40000 ALTER TABLE `game_playerskill` DISABLE KEYS */;
INSERT INTO `game_playerskill` VALUES (1,1,0,6,1,20,5,5,2,100),(2,1,0,3,1,20,5,5,2,100);
/*!40000 ALTER TABLE `game_playerskill` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_quickslot`
--

DROP TABLE IF EXISTS `game_quickslot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_quickslot` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `player_id` bigint NOT NULL,
  `slot_index` smallint unsigned NOT NULL,
  `skill_id` bigint DEFAULT NULL,
  `item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `game_quickslot_player_id_slot_index_0f0d9a2a_uniq` (`player_id`,`slot_index`),
  KEY `game_quickslot_player_id_ea9079c5` (`player_id`),
  KEY `game_quicks_player__3a8bd3_idx` (`player_id`),
  CONSTRAINT `game_quickslot_chk_1` CHECK ((`slot_index` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_quickslot`
--

LOCK TABLES `game_quickslot` WRITE;
/*!40000 ALTER TABLE `game_quickslot` DISABLE KEYS */;
INSERT INTO `game_quickslot` VALUES (1,6,1,1,NULL);
/*!40000 ALTER TABLE `game_quickslot` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_skill`
--

DROP TABLE IF EXISTS `game_skill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_skill` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` longtext NOT NULL,
  `battle_description` longtext NOT NULL,
  `level` smallint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `game_skill_chk_1` CHECK ((`level` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_skill`
--

LOCK TABLES `game_skill` WRITE;
/*!40000 ALTER TABLE `game_skill` DISABLE KEYS */;
INSERT INTO `game_skill` VALUES (1,'普通攻击','','',1);
/*!40000 ALTER TABLE `game_skill` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_team`
--

DROP TABLE IF EXISTS `game_team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_team` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `max_size` smallint unsigned NOT NULL,
  `need_approval` tinyint(1) NOT NULL,
  `leader_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_team_leader_id_98cb1ce9_fk_game_player_id` (`leader_id`),
  CONSTRAINT `game_team_leader_id_98cb1ce9_fk_game_player_id` FOREIGN KEY (`leader_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_team_chk_1` CHECK ((`max_size` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_team`
--

LOCK TABLES `game_team` WRITE;
/*!40000 ALTER TABLE `game_team` DISABLE KEYS */;
INSERT INTO `game_team` VALUES (13,'风火轮的队伍',5,0,6);
/*!40000 ALTER TABLE `game_team` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_teammember`
--

DROP TABLE IF EXISTS `game_teammember`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_teammember` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `join_time` datetime(6) NOT NULL,
  `is_leader` tinyint(1) NOT NULL,
  `player_id` bigint NOT NULL,
  `team_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `game_teammember_player_id_team_id_105ba51a_uniq` (`player_id`,`team_id`),
  KEY `game_teammember_team_id_f041d65d_fk_game_team_id` (`team_id`),
  CONSTRAINT `game_teammember_player_id_ee21ea01_fk_game_player_id` FOREIGN KEY (`player_id`) REFERENCES `game_player` (`id`),
  CONSTRAINT `game_teammember_team_id_f041d65d_fk_game_team_id` FOREIGN KEY (`team_id`) REFERENCES `game_team` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_teammember`
--

LOCK TABLES `game_teammember` WRITE;
/*!40000 ALTER TABLE `game_teammember` DISABLE KEYS */;
INSERT INTO `game_teammember` VALUES (25,'2025-06-12 13:06:02.898912',1,6,13),(26,'2025-06-12 18:21:23.089510',0,3,13);
/*!40000 ALTER TABLE `game_teammember` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_user`
--

DROP TABLE IF EXISTS `game_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(32) NOT NULL,
  `password` varchar(128) NOT NULL,
  `email` varchar(64) DEFAULT NULL,
  `phone` varchar(32) DEFAULT NULL,
  `user_type` smallint unsigned NOT NULL,
  `status` smallint unsigned NOT NULL,
  `security_code` varchar(8) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `last_login_ip` char(39) DEFAULT NULL,
  `last_login_at` datetime(6) DEFAULT NULL,
  `failed_attempts` smallint unsigned NOT NULL,
  `params` json NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `game_user_usernam_2883f6_idx` (`username`),
  KEY `game_user_last_lo_6a9d59_idx` (`last_login_ip`),
  CONSTRAINT `game_user_chk_1` CHECK ((`user_type` >= 0)),
  CONSTRAINT `game_user_chk_2` CHECK ((`status` >= 0)),
  CONSTRAINT `game_user_chk_3` CHECK ((`failed_attempts` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_user`
--

LOCK TABLES `game_user` WRITE;
/*!40000 ALTER TABLE `game_user` DISABLE KEYS */;
INSERT INTO `game_user` VALUES (1,'aaaaaa','aaaaaa',NULL,NULL,1,0,'111111','2025-06-10 12:17:47.845374','127.0.0.1','2025-06-19 16:36:39.033843',0,'{\"persistent_token\": \"H3Vkiu0ZLc6QR_dvgbivWvTxC8gexF9kvaeBfpSNKeU\"}'),(2,'bbbbbb','bbbbbb',NULL,NULL,1,0,'111111','2025-06-10 12:18:59.735607','127.0.0.1','2025-06-11 10:35:40.108339',0,'{\"persistent_token\": \"SqXr3P6Gm3LgHBYdfwPREloBmmS2FgkfC-HgdLnFKAk\"}'),(6,'cccccc','cccccc',NULL,NULL,1,0,'111111','2025-06-10 14:01:36.523152','127.0.0.1','2025-06-19 17:52:11.843603',0,'{\"persistent_token\": \"LE1owk8wuCiA5UIAMCjeLuwM6LYlZtdzEPK5piNtb6o\"}');
/*!40000 ALTER TABLE `game_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `player_equipment`
--

DROP TABLE IF EXISTS `player_equipment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_equipment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `position` smallint unsigned NOT NULL,
  `hp` int NOT NULL,
  `attack` int NOT NULL,
  `defense` int NOT NULL,
  `minjie` int NOT NULL,
  `linghunli` int NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `player_equipment_chk_1` CHECK ((`position` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `player_equipment`
--

LOCK TABLES `player_equipment` WRITE;
/*!40000 ALTER TABLE `player_equipment` DISABLE KEYS */;
/*!40000 ALTER TABLE `player_equipment` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-20  2:15:20
