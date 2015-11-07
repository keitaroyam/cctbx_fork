-- MySQL Script generated by MySQL Workbench
-- Fri Nov  6 14:33:05 2015
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`runs`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`runs` (
  `run_id` INT NOT NULL AUTO_INCREMENT,
  `run` INT NOT NULL,
  `tags` VARCHAR(140) NULL,
  PRIMARY KEY (`run_id`),
  UNIQUE INDEX `run_UNIQUE` (`run` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`rungroups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`rungroups` (
  `rungroup_id` INT NOT NULL AUTO_INCREMENT,
  `startrun` INT NOT NULL,
  `endrun` INT NULL,
  `detz_parameter` DOUBLE NOT NULL,
  `beamx` DOUBLE NULL,
  `beamy` DOUBLE NULL,
  `untrusted_pixel_mask_path` VARCHAR(4097) NULL,
  `dark_avg_path` VARCHAR(4097) NULL,
  `dark_stddev_path` VARCHAR(4097) NULL,
  `gain_map_path` VARCHAR(4097) NULL,
  `binning` INT NULL,
  `usecase` VARCHAR(45) NULL,
  `comment` VARCHAR(1024) NULL,
  PRIMARY KEY (`rungroup_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`trials`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`trials` (
  `trial_id` INT NOT NULL AUTO_INCREMENT,
  `trial` INT NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 0,
  `target_phil_path` VARCHAR(4097) NULL,
  `comment` VARCHAR(1024) NULL,
  PRIMARY KEY (`trial_id`),
  UNIQUE INDEX `trial_UNIQUE` (`trial` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`trial_rungroups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`trial_rungroups` (
  `trial_rungroup_id` INT NOT NULL AUTO_INCREMENT,
  `active` TINYINT(1) NOT NULL DEFAULT 0,
  `rungroups_id` INT NOT NULL,
  `trials_id` INT NOT NULL,
  PRIMARY KEY (`trial_rungroup_id`, `rungroups_id`, `trials_id`),
  INDEX `fk_trial_rungroups_rungroups1_idx` (`rungroups_id` ASC),
  INDEX `fk_trial_rungroups_trials1_idx` (`trials_id` ASC),
  CONSTRAINT `fk_trial_rungroups_rungroups1`
    FOREIGN KEY (`rungroups_id`)
    REFERENCES `mydb`.`rungroups` (`rungroup_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_trial_rungroups_trials1`
    FOREIGN KEY (`trials_id`)
    REFERENCES `mydb`.`trials` (`trial_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`jobs`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`jobs` (
  `job_id` INT NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(45) NULL,
  `runs_id` INT NOT NULL,
  `trials_id` INT NOT NULL,
  `rungroups_id` INT NOT NULL,
  PRIMARY KEY (`job_id`, `runs_id`, `trials_id`, `rungroups_id`),
  INDEX `fk_jobs_runs_idx` (`runs_id` ASC),
  INDEX `fk_jobs_trials1_idx` (`trials_id` ASC),
  INDEX `fk_jobs_rungroups1_idx` (`rungroups_id` ASC),
  CONSTRAINT `fk_jobs_runs`
    FOREIGN KEY (`runs_id`)
    REFERENCES `mydb`.`runs` (`run_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_jobs_trials1`
    FOREIGN KEY (`trials_id`)
    REFERENCES `mydb`.`trials` (`trial_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_jobs_rungroups1`
    FOREIGN KEY (`rungroups_id`)
    REFERENCES `mydb`.`rungroups` (`rungroup_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`isoforms`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`isoforms` (
  `isoform_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NOT NULL,
  `cell_a` DOUBLE NOT NULL,
  `cell_b` DOUBLE NOT NULL,
  `cell_c` DOUBLE NOT NULL,
  `cell_alpha` DOUBLE NOT NULL,
  `cell_beta` DOUBLE NOT NULL,
  `cell_gamma` DOUBLE NOT NULL,
  `lookup_symbol` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`isoform_id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`hkls`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`hkls` (
  `hkl_id` INT NOT NULL AUTO_INCREMENT,
  `h` INT NOT NULL,
  `k` INT NOT NULL,
  `l` INT NOT NULL,
  `isoforms_id` INT NOT NULL,
  PRIMARY KEY (`hkl_id`),
  INDEX `fk_hkls_isoforms1_idx` (`isoforms_id` ASC),
  CONSTRAINT `fk_hkls_isoforms1`
    FOREIGN KEY (`isoforms_id`)
    REFERENCES `mydb`.`isoforms` (`isoform_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`frames`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`frames` (
  `frame_id` INT NOT NULL AUTO_INCREMENT,
  `wavelength` DOUBLE NOT NULL,
  `beam_x` DOUBLE NOT NULL,
  `beam_y` DOUBLE NOT NULL,
  `distance` DOUBLE NOT NULL,
  `sifoil` DOUBLE NOT NULL,
  `c_c` DOUBLE NULL,
  `slope` DOUBLE NULL,
  `offset` DOUBLE NULL,
  `res_ori_1` DOUBLE NULL,
  `res_ori_2` DOUBLE NULL,
  `res_ori_3` DOUBLE NULL,
  `res_ori_4` DOUBLE NULL,
  `res_ori_5` DOUBLE NULL,
  `res_ori_6` DOUBLE NULL,
  `res_ori_7` DOUBLE NULL,
  `res_ori_8` DOUBLE NULL,
  `res_ori_9` DOUBLE NULL,
  `rotation_100_rad` DOUBLE NULL,
  `rotation_010_rad` DOUBLE NULL,
  `rotation_001_rad` DOUBLE NULL,
  `mosaic_block_rotation` DOUBLE NULL,
  `mosaic_block_size` DOUBLE NULL,
  `green_curve_volume` DOUBLE NULL,
  `eventstamp` VARCHAR(45) NOT NULL,
  `timestamp` TIMESTAMP NOT NULL DEFAULT NOW(),
  `unique_file_name` MEDIUMTEXT NULL,
  `rungroups_id` INT NOT NULL,
  `trials_id` INT NOT NULL,
  `isoforms_id` INT NOT NULL,
  PRIMARY KEY (`frame_id`, `rungroups_id`, `trials_id`),
  INDEX `fk_frames_rungroups1_idx` (`rungroups_id` ASC),
  INDEX `fk_frames_trials1_idx` (`trials_id` ASC),
  INDEX `fk_frames_isoforms1_idx` (`isoforms_id` ASC),
  CONSTRAINT `fk_frames_rungroups1`
    FOREIGN KEY (`rungroups_id`)
    REFERENCES `mydb`.`rungroups` (`rungroup_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_frames_trials1`
    FOREIGN KEY (`trials_id`)
    REFERENCES `mydb`.`trials` (`trial_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_frames_isoforms1`
    FOREIGN KEY (`isoforms_id`)
    REFERENCES `mydb`.`isoforms` (`isoform_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`observations`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`observations` (
  `obs_id` INT NOT NULL AUTO_INCREMENT,
  `i` DOUBLE NOT NULL COMMENT '                 ',
  `sigi` DOUBLE NOT NULL,
  `panel` INT NOT NULL,
  `detector_x_px` DOUBLE NOT NULL,
  `detector_y_px` DOUBLE NOT NULL,
  `overload_flag` TINYINT(1) NOT NULL DEFAULT 0,
  `original_h` INT NOT NULL,
  `original_k` INT NOT NULL,
  `original_l` INT NOT NULL,
  `hkls_id` INT NOT NULL,
  `frames_id` INT NOT NULL,
  `frames_rungroups_id` INT NOT NULL,
  `frames_trials_id` INT NOT NULL,
  PRIMARY KEY (`obs_id`, `hkls_id`, `frames_id`, `frames_rungroups_id`, `frames_trials_id`),
  INDEX `fk_observations_hkls1_idx` (`hkls_id` ASC),
  INDEX `fk_observations_frames1_idx` (`frames_id` ASC, `frames_rungroups_id` ASC, `frames_trials_id` ASC),
  CONSTRAINT `fk_observations_hkls1`
    FOREIGN KEY (`hkls_id`)
    REFERENCES `mydb`.`hkls` (`hkl_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_observations_frames1`
    FOREIGN KEY (`frames_id` , `frames_rungroups_id` , `frames_trials_id`)
    REFERENCES `mydb`.`frames` (`frame_id` , `rungroups_id` , `trials_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
