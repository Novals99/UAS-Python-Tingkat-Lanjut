-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.0.30 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             12.17.0.7270
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for db_krs
CREATE DATABASE IF NOT EXISTS `db_krs` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `db_krs`;

-- Dumping structure for table db_krs.krs
CREATE TABLE IF NOT EXISTS `krs` (
  `thn_ajar` int NOT NULL,
  `semester` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nim` int NOT NULL,
  `kodemk` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`thn_ajar`,`semester`,`nim`,`kodemk`),
  KEY `nim` (`nim`),
  KEY `kodemk` (`kodemk`),
  CONSTRAINT `krs_ibfk_1` FOREIGN KEY (`nim`) REFERENCES `mahasiswa` (`nim`),
  CONSTRAINT `krs_ibfk_2` FOREIGN KEY (`kodemk`) REFERENCES `matakuliah` (`kodemk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table db_krs.krs: ~0 rows (approximately)
INSERT INTO `krs` (`thn_ajar`, `semester`, `nim`, `kodemk`) VALUES
	(2026, '2', 111111, 'MK001'),
	(2026, '2', 111111, 'MK002'),
	(2026, '2', 123456, 'MK001'),
	(2026, '2', 123456, 'MK002');

-- Dumping structure for table db_krs.mahasiswa
CREATE TABLE IF NOT EXISTS `mahasiswa` (
  `nim` int NOT NULL,
  `nama` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `jurusan` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fakultas` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`nim`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table db_krs.mahasiswa: ~0 rows (approximately)
INSERT INTO `mahasiswa` (`nim`, `nama`, `jurusan`, `fakultas`) VALUES
	(98765, 'Rivendy', 'Akuntansi Bisnis', 'Ekonomi dan Bisnis'),
	(111111, 'Foreal Nagatomo', 'Teknik Informatika', 'Teknologi Informasi'),
	(123456, 'Naufal Sanjayuy', 'Sistem Informasi', 'Teknologi Informasi');

-- Dumping structure for table db_krs.matakuliah
CREATE TABLE IF NOT EXISTS `matakuliah` (
  `kodemk` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `namamk` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sks` int DEFAULT NULL,
  `biaya` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`kodemk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table db_krs.matakuliah: ~0 rows (approximately)
INSERT INTO `matakuliah` (`kodemk`, `namamk`, `sks`, `biaya`) VALUES
	('MK001', 'Perancangan Basis Data', 3, 400000.00),
	('MK002', 'Python Tingkat Lanjut', 3, 400000.00),
	('MK003', 'Aplikasi Wawasan Budi Luhur', 1, 200000.00);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
