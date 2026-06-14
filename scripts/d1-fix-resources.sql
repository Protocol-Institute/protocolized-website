-- Fix garbled/boilerplate descriptions and metadata errors in D1

UPDATE resources SET description = 'The Summer of Protocols 2023 retrospective anthology — a collected volume of research papers, essays, and creative works from the inaugural year of the program.' WHERE slug = '2023-retrospectus';

UPDATE resources SET description = 'A phenomenological examination of protocols by Janna Tay — exploring how the rules and standards that govern coordination shape lived experience, perception, and the texture of everyday life.' WHERE slug = 'a-phenomenology-of-protocols';

UPDATE resources SET description = 'Chenoe Hart explores how protocols create addressable, navigable space — examining the relationship between spatial organization, naming systems, and the infrastructure that makes locations findable and reachable.' WHERE slug = 'addressable-space-pdf';

UPDATE resources SET description = 'Kei Kreutler investigates artificial memory systems and the protocols that orient knowledge across vast scales — exploring how human and computational memory might be structured to navigate infinite information landscapes.' WHERE slug = 'artificial-memory-and-orienting-infinity-pdf';

UPDATE resources SET description = 'Josh Stark compares three fundamental coordination mechanisms — physical materials, legal institutions, and blockchains — as distinct protocol systems with different guarantees, failure modes, and affordances.' WHERE slug = 'atoms-institutes-blockchains';

UPDATE resources SET description = 'Trent Van Epps examines how capital and enclosure dynamics shape software commons, drawing on the histories of Linux and Ethereum to analyze tensions between open protocol ecosystems and commercial capture.' WHERE slug = 'capital-enclosure-for-software-commons';

UPDATE resources SET description = 'Saffron Huang explores how protocols shape our experience and control of time — examining the relationship between temporal coordination mechanisms, human consciousness, and the social structures that govern when and how we act.' WHERE slug = 'control-and-consciousness-of-time';

UPDATE resources SET description = 'Shreeda Segan explores romantic and social matching through the lens of protocol — how dating apps, courtship rituals, and social scripts function as coordination protocols with unintended consequences for connection and community.' WHERE slug = 'dangerous-dating-protocols';

UPDATE resources SET description = 'Nadia Asparouhova examines the dark potential of protocols — how coordination systems can be captured, weaponized, or designed in ways that cause harm, and what makes certain protocols dangerous.' WHERE slug = 'dangerous-protocols';

UPDATE resources SET description = 'Rithikha Rajamohan''s field dispatches from the Pacific Northwest explore regional governance and ecological protocols — examining how place, community, and environment shape the protocols people create to live together.' WHERE slug = 'dispatches-from-cascadia';

UPDATE resources SET description = 'Every protocol deserves a second chance. ActivityPub (2018) is the distributed social network protocol, developed before end-to-end encryption (E2EE) was standard practice. A case file exploring how to bring E2EE to ActivityPub.' WHERE slug = 'end-to-end-encryption-in-activitypub-case-file';

UPDATE resources SET description = 'Shuya Gong examines exit rights and protocol design — exploring how individuals and communities can exercise meaningful exit from coordination systems, and what protocols must look like to enable genuine choice and voice.' WHERE slug = 'exit-to-protocol';

UPDATE resources SET description = 'After a century of fire suppression and heating atmospheric conditions, California has changed from a fire-ecology to a fire-climate. A case file exploring how our renewed ability to work with fire is reshaping environmental knowledge and protocol.' WHERE slug = 'fire-protocols-case-file';

UPDATE resources SET description = 'Sarah Friend investigates the protocols of dying — how end-of-life is structured by medical, legal, social, and cultural coordination systems, and what a ''good death'' might require from the protocols that govern it.' WHERE slug = 'good-death-pdf';

UPDATE resources SET description = 'A case file imagining a future where decision-making and resource allocation are driven by nuanced voting protocols that consider voter identity and expertise, moving beyond the limitations of traditional one-person-one-vote systems.' WHERE slug = 'plurality-in-practice-case-file';

UPDATE resources SET description = 'Drew Austin applies the pattern language concept to protocol design — collecting recurring structural patterns, anti-patterns, and design templates for building effective coordination systems across urban and digital spaces.' WHERE slug = 'protocol-pattern-language-anthology';

UPDATE resources SET description = 'Dorian Taylor examines how the web''s foundational protocols might be retrofitted to address contemporary challenges — exploring the tension between backward compatibility and the need for meaningful reform of internet infrastructure.' WHERE slug = 'retrofitting-the-web-pdf';

UPDATE resources SET description = 'Timber Stinson-Schroff explores safety as a protocol domain — examining how coordination systems govern risk, precaution, and harm prevention across technical, industrial, and social contexts.' WHERE slug = 'safe-new-world-pdf';

UPDATE resources SET description = 'In a world defined by rising sea levels, can we learn to live better in wetter cities? A case file on sea level rise adaptation and how communities and engineering agencies are developing new protocols for urban water management.' WHERE slug = 'shoreline-adaptations-case-file';

UPDATE resources SET description = 'A Summer of Protocols 2023 research paper by David Lang exploring protocol systems in the context of standards, measurement, and collaborative making.' WHERE slug = 'summer-of-protocols-research-lang';

-- Steiert: fix title, authors, and description
UPDATE resources SET
  title = 'Protocols in (Emergency) Time',
  authors = '[{"name":"Olivia Steiert"}]',
  description = 'Olivia Steiert explores how emergency conditions — from natural disasters to public health crises — reshape and reveal the underlying protocols that govern response, coordination, and collective care under pressure.'
WHERE slug = 'summer-of-protocols-research-steiert';

-- Delete duplicate Steiert entry
DELETE FROM resources WHERE slug = 'summer-of-protocols-research-steiert-1';

UPDATE resources SET description = 'Alice Noujaim analyzes Orkut''s rise and fall as a case study in social network protocol death — examining what happens when coordination platforms lose critical mass, and what digital communities leave behind when they collapse.' WHERE slug = 'the-death-and-the-death-of-orkut';

UPDATE resources SET description = 'Angela Walch provides a foundational analysis of how protocol systems are structured, maintained, and governed — with particular attention to power dynamics, accountability gaps, and the fiction of protocol neutrality.' WHERE slug = 'the-fundamentals-of-protocol-systems';

UPDATE resources SET description = 'An anonymous analysis of China''s 2022 Covid protests through the lens of swarm coordination — examining how leaderless, protocol-driven collective action enabled one of the country''s largest waves of public dissent.' WHERE slug = 'the-swarm-effect-chinas-2022-covid-protests';

-- Unreasonable Sufficiency: fix author and description
UPDATE resources SET
  authors = '[{"name":"Josh Stark"},{"name":"Trent Van Epps"},{"name":"Bastian Aue"}]',
  description = 'Josh Stark, Trent Van Epps, and Bastian Aue argue that protocols are a surprisingly sufficient foundation for coordination at scale — making the case that apparent protocol simplicity belies transformative power across social, technical, and institutional domains.'
WHERE slug = 'the-unreasonable-sufficiency-of-protocols';

UPDATE resources SET description = 'Spencer Chang explores memory as protocol — examining how communities weave collective memory through practices, artifacts, and coordination systems, and what it means to design protocols that preserve and transmit what matters.' WHERE slug = 'weaving-memory';
