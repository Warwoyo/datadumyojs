-- OJS 2.4.8-4 upload-directory SAST dataset — data-only baseline seed.
-- Generated 2026-06-21T16:14:24Z. Benign content only; INERT scenario artifacts live in
-- scenarios/*/overlay-files and are NOT part of this baseline.
--
-- Apply on a freshly-installed OJS 2.4.8-4 schema (or the reference schema
-- in scripts/lib/schema_to_mysql.py). Does not create tables or touch source.
SET NAMES utf8;
SET FOREIGN_KEY_CHECKS=0;
START TRANSACTION;

-- journals
INSERT INTO `journals` (`journal_id`, `path`, `seq`, `primary_locale`, `enabled`) VALUES (1, 'jdis', 1, 'en_US', 1);

-- journal_settings
INSERT INTO `journal_settings` (`journal_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'title', 'Journal of Dummy Information Systems', 'string');
INSERT INTO `journal_settings` (`journal_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'publisherInstitution', 'Laboratory Publisher', 'string');
INSERT INTO `journal_settings` (`journal_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, '', 'onlineIssn', '2789-0000', 'string');
INSERT INTO `journal_settings` (`journal_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, '', 'supportedLocales', 'a:1:{i:0;s:5:"en_US";}', 'object');

-- users
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (1, 'siteadmin', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Sam', 'Admin', 'siteadmin@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (2, 'manager01', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Mira', 'Manager', 'manager01@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (3, 'editor01', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Edi', 'Editor', 'editor01@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (4, 'editor02', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Sek', 'Sectioneditor', 'editor02@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (5, 'reviewer01', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Rev', 'Onewer', 'reviewer01@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (6, 'reviewer02', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Rini', 'Twower', 'reviewer02@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (7, 'author01', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Ari', 'Authorone', 'author01@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (8, 'author02', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Bayu', 'Authortwo', 'author02@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (9, 'author03', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Cinta', 'Authorthree', 'author03@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (10, 'author04', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Dito', 'Authorfour', 'author04@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);
INSERT INTO `users` (`user_id`, `username`, `password`, `first_name`, `last_name`, `email`, `date_registered`, `date_last_login`, `disabled`, `must_change_password`, `inline_help`) VALUES (11, 'reader01', '$2y$12$XUPLCo8Xnasv7oHs7q.Mt.0SFlqtPBCRkiVM2dwa2Ia32412qKl5y', 'Rian', 'Reader', 'reader01@example.invalid', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 0, 1, 1);

-- roles
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (0, 1, 1);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 2, 16);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 3, 256);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 4, 512);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 5, 4096);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 6, 4096);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 7, 65536);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 8, 65536);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 9, 65536);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 10, 65536);
INSERT INTO `roles` (`journal_id`, `user_id`, `role_id`) VALUES (1, 11, 1048576);

-- sections
INSERT INTO `sections` (`section_id`, `journal_id`, `seq`, `editor_restricted`, `meta_indexed`, `meta_reviewed`, `abstracts_not_required`, `hide_title`, `hide_author`, `hide_about`, `disable_comments`) VALUES (1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0);
INSERT INTO `sections` (`section_id`, `journal_id`, `seq`, `editor_restricted`, `meta_indexed`, `meta_reviewed`, `abstracts_not_required`, `hide_title`, `hide_author`, `hide_about`, `disable_comments`) VALUES (2, 1, 2, 0, 1, 1, 0, 0, 0, 0, 0);

-- section_settings
INSERT INTO `section_settings` (`section_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'title', 'Artikel', 'string');
INSERT INTO `section_settings` (`section_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'abbrev', 'ART', 'string');
INSERT INTO `section_settings` (`section_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (2, 'en_US', 'title', 'Tinjauan', 'string');
INSERT INTO `section_settings` (`section_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (2, 'en_US', 'abbrev', 'REV', 'string');

-- issues
INSERT INTO `issues` (`issue_id`, `journal_id`, `volume`, `number`, `year`, `published`, `current`, `date_published`, `access_status`, `show_volume`, `show_number`, `show_year`, `show_title`) VALUES (1, 1, 1, '1', 2025, 1, 1, '2026-06-21 09:00:00', 1, 1, 1, 1, 1);
INSERT INTO `issues` (`issue_id`, `journal_id`, `volume`, `number`, `year`, `published`, `current`, `date_published`, `access_status`, `show_volume`, `show_number`, `show_year`, `show_title`) VALUES (2, 1, 1, '2', 2026, 0, 0, NULL, 1, 1, 1, 1, 1);

-- issue_settings
INSERT INTO `issue_settings` (`issue_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'title', 'Inaugural Published Issue', 'string');
INSERT INTO `issue_settings` (`issue_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (2, 'en_US', 'title', 'Future Issue', 'string');

-- issue_files
INSERT INTO `issue_files` (`file_id`, `issue_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `content_type`, `date_uploaded`, `date_modified`) VALUES (1, 1, '1-1-PB.jpg', 'image/jpeg', 160, 'cover-issue-1.jpg', 1, '2026-06-21 09:00:00', '2026-06-21 09:00:00');

-- articles
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (1, 'en_US', 7, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 1, '1-10', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (2, 'en_US', 8, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 2, '2-11', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (3, 'en_US', 9, 1, 2, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 4, '3-12', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (4, 'en_US', 10, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 6, '4-13', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (5, 'en_US', 7, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 8, '5-14', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (6, 'en_US', 8, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 3, 0, 1, 10, '6-15', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (7, 'en_US', 9, 1, 2, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 12, '7-16', 0, 0, 0);
INSERT INTO `articles` (`article_id`, `locale`, `user_id`, `journal_id`, `section_id`, `language`, `date_submitted`, `last_modified`, `date_status_modified`, `status`, `submission_progress`, `current_round`, `submission_file_id`, `pages`, `fast_tracked`, `hide_author`, `comments_status`) VALUES (8, 'en_US', 10, 1, 1, 'en', '2026-06-21 09:00:00', '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1, 0, 1, 14, '8-17', 0, 0, 0);

-- article_settings
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'title', 'A Reproducible Pipeline for Dummy Information Systems', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (1, 'en_US', 'abstract', '<p>Synthetic abstract for article 1.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (2, 'en_US', 'title', 'Peer Review Dynamics in Synthetic Journals', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (2, 'en_US', 'abstract', '<p>Synthetic abstract for article 2.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (3, 'en_US', 'title', 'Editorial Decision Modelling: A Review', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (3, 'en_US', 'abstract', '<p>Synthetic abstract for article 3.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (4, 'en_US', 'title', 'Copyediting Workflows for Lab Datasets', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (4, 'en_US', 'abstract', '<p>Synthetic abstract for article 4.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (5, 'en_US', 'title', 'Layout and Typesetting of Dummy Manuscripts', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (5, 'en_US', 'abstract', '<p>Synthetic abstract for article 5.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (6, 'en_US', 'title', 'A Published Study on Upload Directory Structure', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (6, 'en_US', 'abstract', '<p>Synthetic abstract for article 6.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (7, 'en_US', 'title', 'Supplementary Data Handling in OJS 2.4', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (7, 'en_US', 'abstract', '<p>Synthetic abstract for article 7.</p>', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (8, 'en_US', 'title', 'Revision Tracking Across Multiple File Versions', 'string');
INSERT INTO `article_settings` (`article_id`, `locale`, `setting_name`, `setting_value`, `setting_type`) VALUES (8, 'en_US', 'abstract', '<p>Synthetic abstract for article 8.</p>', 'string');

-- article_files
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (1, 1, 1, '1-1-1-SM.pdf', 'application/pdf', 763, 'sm-a001.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (2, 1, 2, '2-2-1-SM.pdf', 'application/pdf', 752, 'sm-a002.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (3, 1, 2, '2-3-1-RV.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1024, 'rv-a002.docx', 2, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (4, 1, 3, '3-4-1-SM.pdf', 'application/pdf', 748, 'sm-a003.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (5, 1, 3, '3-5-1-ED.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1025, 'ed-a003.docx', 3, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (6, 1, 4, '4-6-1-SM.pdf', 'application/pdf', 748, 'sm-a004.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (7, 1, 4, '4-7-1-CE.odt', 'application/vnd.oasis.opendocument.text', 796, 'ce-a004.odt', 4, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (8, 1, 5, '5-8-1-SM.pdf', 'application/pdf', 753, 'sm-a005.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (9, 1, 5, '5-9-1-LE.pdf', 'application/pdf', 753, 'le-a005.pdf', 5, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (10, 1, 6, '6-10-1-SM.pdf', 'application/pdf', 757, 'sm-a006.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (11, 1, 6, '6-11-1-PB.pdf', 'application/pdf', 757, 'pb-a006.pdf', 6, 1, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (12, 1, 7, '7-12-1-SM.pdf', 'application/pdf', 748, 'sm-a007.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (13, 1, 7, '7-13-1-SP.csv', 'text/csv', 105, 'sp-a007.csv', 7, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (14, 1, 8, '8-14-1-SM.pdf', 'application/pdf', 757, 'sm-a008.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);
INSERT INTO `article_files` (`file_id`, `revision`, `article_id`, `file_name`, `file_type`, `file_size`, `original_file_name`, `file_stage`, `viewable`, `date_uploaded`, `date_modified`, `round`) VALUES (14, 2, 8, '8-14-2-SM.pdf', 'application/pdf', 757, 'sm-a008.pdf', 1, 0, '2026-06-21 09:00:00', '2026-06-21 09:00:00', 1);

-- article_supplementary_files
INSERT INTO `article_supplementary_files` (`supp_id`, `file_id`, `article_id`, `type`, `language`, `date_created`, `show_reviewers`, `date_submitted`, `seq`) VALUES (1, 13, 7, '', 'en_US', '2026-06-21', 1, '2026-06-21 09:00:00', 1);

-- article_galleys
INSERT INTO `article_galleys` (`galley_id`, `locale`, `article_id`, `file_id`, `label`, `html_galley`, `seq`) VALUES (1, 'en_US', 6, 11, 'PDF', 0, 1);

-- published_articles
INSERT INTO `published_articles` (`published_article_id`, `article_id`, `issue_id`, `date_published`, `seq`, `access_status`) VALUES (1, 6, 1, '2026-06-21 09:00:00', 6, 1);

COMMIT;
SET FOREIGN_KEY_CHECKS=1;
