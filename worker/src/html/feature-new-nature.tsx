import { Base } from "./base";
import { mobileMenuScript } from "./static-pages";

const R2 = "https://files.protocolized.io/features/new-nature";

const css = `
  .essay-body {
    font-family: 'Lora', Georgia, serif;
    font-size: 19px;
    line-height: 1.72;
    color: #2C2C2A;
  }
  .essay-body h2 {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.55em;
    font-weight: normal;
    font-style: italic;
    margin: 3em 0 0.7em;
    color: #2C2C2A;
  }
  .essay-body h3 {
    font-family: 'Outfit', sans-serif;
    font-size: 0.95em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 2.5em 0 0.6em;
    color: #0F6E56;
  }
  .essay-body p { margin: 0 0 1.15em; }
  .essay-body ul { margin: 0 0 1.15em; padding-left: 1.6em; }
  .essay-body ul li { margin-bottom: 0.35em; }
  .essay-body a { color: #0F6E56; }
  .essay-body a:hover { color: #085041; }
  .essay-body hr { border: none; border-top: 1px solid #e2e0da; margin: 3.5em 0; }

  .essay-note {
    font-family: 'Outfit', sans-serif;
    font-size: 0.8em;
    color: #888;
    font-style: italic;
    margin: 0.8em 0 1.4em;
    padding-left: 1em;
    border-left: 2px solid #ddd;
  }

  figure { margin: 2em 0; }
  figure img { max-width: 100%; display: block; }
  figure.narrow { max-width: 58%; }
  figure.medium { max-width: 75%; }
  figcaption {
    font-family: 'Outfit', sans-serif;
    font-size: 0.73em;
    color: #999;
    margin-top: 7px;
    line-height: 1.45;
  }
  .fig-row { display: flex; gap: 14px; margin: 2em 0; align-items: flex-start; }
  .fig-row figure { flex: 1; margin: 0; }

  .formula-box {
    border: 1px solid #c8e8df;
    background: #E1F5EE;
    padding: 24px 32px;
    margin: 2em 0;
    text-align: center;
    border-radius: 2px;
  }
  .formula-box .formula {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.65em;
    letter-spacing: 0.02em;
    margin-bottom: 0.5em;
    color: #0F6E56;
  }
  .formula-box .gloss {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82em;
    color: #085041;
  }

  table.evil-twins {
    width: 100%;
    border-collapse: collapse;
    margin: 1.8em 0;
    font-family: 'Outfit', sans-serif;
    font-size: 0.84em;
    line-height: 1.45;
  }
  table.evil-twins thead th {
    text-align: left;
    padding: 8px 14px;
    border-bottom: 2px solid #2C2C2A;
    font-weight: 700;
    font-size: 0.95em;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  table.evil-twins thead th:nth-child(2) { border-left: 1px solid #bbb; }
  table.evil-twins tbody td {
    padding: 6px 14px;
    border-bottom: 1px solid #e8e6e0;
    vertical-align: top;
  }
  table.evil-twins tbody td:nth-child(2) { border-left: 1px solid #e8e6e0; }
  table.evil-twins tbody tr:last-child td {
    font-weight: 700;
    border-bottom: none;
    padding-top: 10px;
  }

  .yt-embed {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    overflow: hidden;
    margin: 2em 0;
  }
  .yt-embed iframe {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    border: none;
  }

  /* slide carousel */
  .carousel { position: relative; margin: 2.5em 0; background: #111; border-radius: 4px; }
  .carousel-viewport { overflow: hidden; border-radius: 4px 4px 0 0; }
  .carousel-track { display: flex; transition: transform 0.35s ease; }
  .carousel-slide { min-width: 100%; flex-shrink: 0; }
  .carousel-slide figure { margin: 0; }
  .carousel-slide img { width: 100%; height: auto; display: block; max-height: 520px; object-fit: contain; background: #111; }
  .carousel-slide figcaption { padding: 0.7em 1.1em 0.8em; background: #1a1a1a; color: #bbb; font-size: 0.76em; line-height: 1.5; font-family: 'Outfit', sans-serif; font-style: italic; }
  .carousel-btn { position: absolute; top: 38%; transform: translateY(-50%); background: rgba(0,0,0,0.52); color: #fff; border: none; width: 38px; height: 54px; font-size: 1.15em; cursor: pointer; z-index: 10; display: flex; align-items: center; justify-content: center; transition: background 0.18s; }
  .carousel-btn:hover { background: rgba(0,0,0,0.82); }
  .carousel-prev { left: 0; border-radius: 0 3px 3px 0; }
  .carousel-next { right: 0; border-radius: 3px 0 0 3px; }
  .carousel-footer { background: #111; padding: 0.45em 1em; border-radius: 0 0 4px 4px; text-align: center; }
  .carousel-counter { font-family: 'Outfit', sans-serif; font-size: 0.72em; color: #555; letter-spacing: 0.06em; }

  /* related resources footer */
  .essay-related {
    margin-top: 4em;
    padding-top: 2em;
    border-top: 2px solid #e2e0da;
  }
  .essay-related h2 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.72em !important;
    font-weight: 700 !important;
    font-style: normal !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #aaa !important;
    margin: 0 0 1.2em !important;
  }
  .related-cards { display: flex; flex-wrap: wrap; gap: 14px; }
  .related-card {
    flex: 1;
    min-width: 200px;
    background: #fff;
    border: 1px solid #e2e0da;
    border-radius: 4px;
    padding: 16px 18px;
    text-decoration: none;
    transition: border-color 0.15s;
  }
  .related-card:hover { border-color: #0F6E56; }
  .related-card-type {
    font-family: 'Outfit', sans-serif;
    font-size: 0.65em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #0F6E56;
    margin-bottom: 4px;
  }
  .related-card-title {
    font-family: 'Lora', Georgia, serif;
    font-size: 0.95em;
    color: #2C2C2A;
    line-height: 1.4;
  }

  @media (max-width: 640px) {
    .fig-row { flex-direction: column; }
    figure.narrow, figure.medium { max-width: 100%; }
    .related-cards { flex-direction: column; }
  }
`;

const carouselScript = `
(function() {
  document.querySelectorAll('.carousel').forEach(function(carousel) {
    var track = carousel.querySelector('.carousel-track');
    var slides = carousel.querySelectorAll('.carousel-slide');
    var counter = carousel.querySelector('.carousel-counter');
    var total = slides.length;
    var idx = 0;
    function go(n) {
      idx = (n + total) % total;
      track.style.transform = 'translateX(-' + idx * 100 + '%)';
      if (counter) counter.textContent = (idx + 1) + ' / ' + total;
    }
    carousel.querySelector('.carousel-prev').addEventListener('click', function() { go(idx - 1); });
    carousel.querySelector('.carousel-next').addEventListener('click', function() { go(idx + 1); });
    go(0);
  });
})();
`;

export function NewNatureFeaturePage({ currentPath }: { currentPath: string }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "New Nature",
    author: { "@type": "Person", name: "Venkatesh Rao" },
    datePublished: "2026-06-17",
    publisher: { "@type": "Organization", name: "Protocol Institute" },
    url: "https://protocolized.io/features/new-nature",
    description:
      "An edited essay version of a June 2026 talk unpacking the Protocol Institute's core thesis: New Nature = AI and Protocols entangled at planetary scale.",
  };

  return (
    <Base
      title="New Nature"
      description="An edited essay version of a June 2026 talk unpacking the Protocol Institute's core thesis: New Nature = AI and Protocols entangled at planetary scale."
      jsonLd={jsonLd}
      ogImage={`${R2}/slides/slide-14.png`}
      currentPath={currentPath}
      bodyScript={mobileMenuScript() + "\n" + carouselScript}
    >
      <style dangerouslySetInnerHTML={{ __html: css }} />

      {/* Feature header */}
      <div class="bg-[#0F6E56] text-white">
        <div class="max-w-[760px] mx-auto px-6 py-10">
          <div class="flex items-center gap-2 mb-4">
            <span class="font-sans text-[0.65em] font-semibold tracking-[0.12em] uppercase bg-white/20 text-white px-2 py-0.5 rounded">
              Special Feature
            </span>
          </div>
          <h1 class="font-serif text-5xl lg:text-6xl font-normal leading-tight mb-3">
            New Nature
          </h1>
          <p class="font-sans text-[#a8d9ca] text-sm">
            Venkatesh Rao &mdash; June 17, 2026
          </p>
        </div>
      </div>

      {/* Essay body */}
      <div class="max-w-[760px] mx-auto px-6 py-12 pb-24 essay-body">

        <p class="essay-note">
          This essay is an edited version of a live talk given on June 17, 2026, unpacking
          the Protocol Institute&apos;s evolving thesis in a more digestible form.
        </p>

        <p>What I want to talk about today is the big idea shaping the Protocol Institute&apos;s initial research mission. I&apos;ve called it New Nature. It is a thesis that has evolved over the past year, and I&apos;ve written a few essays about it:</p>
        <ul>
          <li><a href="https://protocolized.io/p/inventing-new-nature">Inventing New Nature</a>, May 12, 2026</li>
          <li><a href="https://protocolized.io/p/the-fabric-and-the-brain">The Fabric and the Brain</a>, March 31, 2026</li>
          <li><a href="https://protocolized.io/p/theorizing-protocolization-i-new">Theorizing Protocolization I: New Nature</a>, January 8, 2026</li>
          <li><a href="https://protocolized.io/p/constructing-the-evil-twin-of-ai">Constructing the Evil Twin of AI</a>, October 15, 2025</li>
        </ul>

        <div class="yt-embed">
          <iframe src="https://www.youtube.com/embed/U4lSY7BX228?start=360" allowfullscreen></iframe>
        </div>
        <p class="essay-note">
          <a href="https://files.protocolized.io/features/new-nature-slides.pdf">Download slides (PDF)</a>
          &ensp;&mdash;&ensp;
          <a href="/resources/new-nature-slides">Slides resource entry</a>
        </p>

        <p>Since I&apos;m a Research Director, I should have at least one whiteboard image and one formula. Here&apos;s the core idea:</p>
        <figure>
          <img src={`${R2}/openingwhiteboard_clean.png`} alt="New Nature = integral of AI × Protocols over Planet — whiteboard" loading="lazy" />
          <figcaption>The 80/20 definition, as drawn on the whiteboard at the start of the talk. STEM version: New Nature = ∫(AI × Protocols) over Planet. HSS version: New Nature = AI and Protocols entangled at planetary scale.</figcaption>
        </figure>
        <div class="formula-box">
          <div class="formula">New Nature = ∫<sub>(Planet)</sub> AI × Protocols</div>
          <div class="gloss">New Nature = AI and Protocols entangled at Planetary Scale</div>
        </div>
        <p>This is an 80/20 definition — New Nature is a lot more than the formula captures, and I&apos;ll show you some glimpses of what I mean. But this 20% covers 80% of what&apos;s important about it and why you should care. For the humanities and social science people: <em>New Nature is AI and protocols entangled at planetary scale.</em></p>
        <p>We&apos;ll do three things today. First, I&apos;ll show you how we&apos;re trying to embody New Nature in what we do — show first, then tell. Then we&apos;ll go into the theory. And we&apos;ll end with how we find the money to actually do all this.</p>

        <hr />
        <h2 id="background">Background</h2>
        <p>The Protocol Institute is spinning out of the Summer of Protocols — a three-year program, now winding down, that ran three summer cohorts, brought in more than eighty grantees, and produced four published volumes and a limited-edition Protocol Kit. The transition is from a summer program to a standing institution, inheriting that momentum and reorganizing around an ongoing mission. Two sites: <em>protocol-institute.org</em> for the org itself, <em>protocolized.io</em> as the media and research hub. Currently funded by the Ethereum Foundation through the end of the year, after which we figure out how to sustain it. The mission: full-stack nonprofit research, education, evangelism, and scene-making for the protocolized commons.</p>
        <p>My background is relevant to what follows. I came to this role having worked in every form of research environment — startup, big industrial lab, academia — with a PhD in control theory from Michigan. I&apos;ve spent the last fifteen years as an independent researcher and consultant (Ribbonfarm, now Contraptions). None of those prior environments was quite the right fit for me, which is why I ended up as a free agent. I&apos;m approaching my role at this institute, in part, via a somewhat personal agenda — building the sort of place I always wanted to work at, as part of a class of people with research interests and skills, who don&apos;t fit traditional research institutions. The initial research agenda reflects my own interests to some extent (time and temporality, formal protocol theory, psychohistory, robotics) but is increasingly being shaped by others, and will grow broader.</p>
        <div class="fig-row">
          <figure>
            <img src={`${R2}/slides/slide-02.png`} alt="Background: Protocol Institute" loading="lazy" />
          </figure>
          <figure>
            <img src={`${R2}/slides/slide-04.png`} alt="Background: Venkatesh Rao" loading="lazy" />
          </figure>
        </div>

        <hr />
        <h2 id="facilities-tour">Facilities Tour</h2>
        <p>Before I get into it, you should take a tour of both this website (<a href="https://protocol-institute.org">protocol-institute.org</a>) and the companion media hub website (<a href="https://protocolized.io">protocolized.io</a>), and perhaps also join the <a href="https://discord.gg/Z3fgsW8D4s">Discord</a> and browse some of the live conversations. The idea of New Nature becomes more intuitive once you see how we&apos;re already pursuing it. If you&apos;re not already familiar with our activities, take a tour and then come back here to continue reading.</p>
        <figure>
          <img src={`${R2}/slides/slide-05.png`} alt="Facilities Highlights Tour — Flaubert Protocol" loading="lazy" />
          <figcaption>&ldquo;Be regular and orderly in your life, so that you may be violent and original in your work.&rdquo; — Gustave Flaubert</figcaption>
        </figure>

        <hr />
        <h2 id="what-is-new-nature">What Is New Nature?</h2>
        <figure class="narrow">
          <img src={`${R2}/slides/slide-06.png`} alt="What is New Nature? But first, what the hell is nature?" loading="lazy" />
        </figure>
        <p>Assuming you&apos;ve taken a tour of our activities — the hopefully &ldquo;regular and orderly&rdquo; practice of what we&apos;re doing, the &ldquo;violent and original&rdquo; aspirations should start to make more sense.</p>
        <p>What is New Nature? I gave you the 80/20 definition up front. But before diving deep, there&apos;s a prior question worth sitting with: what the hell is <em>nature</em>, exactly?</p>
        <p>As it turns out, nature — in the way we think of it — isn&apos;t something given from nature itself. It&apos;s a construct, a concept that had to be invented at one point. There&apos;s a great book by Andrea Wulf called <em><a href="https://en.wikipedia.org/wiki/The_Invention_of_Nature">The Invention of Nature</a></em>, a biography of Alexander von Humboldt. He&apos;s the person who basically invented nature in the early 19th century. We&apos;ve taken a lot of cues from his work in thinking about what we&apos;re doing with New Nature.</p>
        <div class="fig-row">
          <figure>
            <img src={`${R2}/slides/slide-07.png`} alt="Nature had to be invented — Humboldt portrait and book cover" loading="lazy" />
          </figure>
          <figure>
            <img src={`${R2}/slides/slide-08.png`} alt="Genesis: Mt. Chimborazo diagram (Humboldt, 1807)" loading="lazy" />
            <figcaption>The Chimborazo diagram (1807) — the first ecological cross-section of a mountain.</figcaption>
          </figure>
        </div>
        <p>Humboldt was an explorer and scientist. In the late 1790s he went to South America, climbed a bunch of mountains, went through forests. At Mount Chimborazo he made this diagram — the ecosystem and ecology of the mountain, showing species distributions by elevation. It was the first time anyone had ever looked at nature this way. It became a hugely popular graphic and a famous artifact in the history of science.</p>
        <p>Later in his life he wrote <em>Cosmos</em>, laying out almost everything we now recognize as our understanding of nature — from time zones to eco zones to isoclines. Humboldt&apos;s <em>Cosmos</em> constructed what we now understand as nature.</p>
        <figure>
          <img src={`${R2}/slides/slide-09.png`} alt="Humboldt's Cosmos constructed Nature (1845–1862)" loading="lazy" />
          <figcaption>Pages from <em>Cosmos</em> (1845–1862).</figcaption>
        </figure>
        <figure>
          <img src={`${R2}/slides/slide-10.png`} alt="Our understanding of nature is Humboldtian — concept map" loading="lazy" />
          <figcaption>Half the vocabulary we use when talking about nature comes from the thinking he did.</figcaption>
        </figure>
        <p>Words we are very familiar with — bioregions, ecological webs, keystone species, ecology and ecosystems, the conservation movement, habitat destruction and preservation, national park systems — all of that came out of Humboldt&apos;s work. He influenced John Muir, Theodore Roosevelt, the Jena Set (German Romantic movement), the English Romantic poets, the American transcendentalists. He was the model for Goethe&apos;s Faust. He anticipated Darwin&apos;s theories, plate tectonics, our understanding of climate change, even cybernetics — he influenced a lot of South American cybernetics thinkers. And he was the first major critic of the effects of industrial agriculture.</p>
        <p>The important thing: Humboldt came up with an understanding of nature that brought the scientific objective view and the poetic-subjective view back together. The Enlightenment had split them apart. The German Romantics tried to pull them back together. Humboldt was the gestalt integrator.</p>
        <figure>
          <img src={`${R2}/slides/slide-11.png`} alt="Nature before Humboldt" loading="lazy" />
        </figure>
        <p>But look at the state of understanding of nature <em>before</em> Humboldt. In the popular imagination: animistic beliefs. In the European elite: authoritarian high-modernism — nature as a set of resources to exploit. Scholarly understanding was rooted in theology: biblical creation stories, Noah&apos;s Ark. Carolus Linnaeus had invented modern biological taxonomy, but that was reductionist and Aristotelian — objective, blind to emergence and gestalt, unable to comprehend the biosphere and geography as categories at all. And critically: no concept of the <em>planetary</em>. Natural wilderness was simply understood as something to be civilized — in exactly the same mindset as colonialism.</p>
        <figure class="narrow">
          <img src={`${R2}/slides/slide-13.png`} alt="What is New Nature? — transition, nature crossed out" loading="lazy" />
          <figcaption>&ldquo;But first, what the hell is nature?&rdquo; — struck through. The detour is over.</figcaption>
        </figure>
        <p>That&apos;s what nature was — and that&apos;s still substantially our understanding of nature nearly two centuries later. Now we can ask: what is <em>New</em> Nature?</p>
        <figure>
          <img src={`${R2}/slides/slide-14.png`} alt="So... What is New Nature? — concept map" loading="lazy" />
          <figcaption>The New Nature concept map. The parallel structure to the Humboldtian concept map is intentional.</figcaption>
        </figure>
        <p>We can make a very similar concept map. You start substituting all the natural, old-nature elements Humboldt was thinking about — working before the industrial revolution, mainly looking at the natural environment — with their counterparts two and a half centuries into the industrial and post-industrial world.</p>
        <p>Instead of plate tectonics: planetary infrastructures. Instead of climate change: terraforming and climate tech. Instead of ecology: the convergence of natural and artificial in AI. Instead of the Romantic movement: the emerging genre of protocol art — there&apos;s an exhibit called &ldquo;Strange New Rules&rdquo; at this year&apos;s Venice Biennale, by the Serpentine Gallery and the Berggruen Institute, which we had a hand in shaping; the name is ours. Instead of keystone species: charismatic technologies. Tim Baker on our team likes to ask: what&apos;s the TSMC of protocols? That&apos;s a New Nature type of question.</p>
        <figure>
          <img src={`${R2}/slides/slide-15.png`} alt="New Nature before Protocol Institute" loading="lazy" />
        </figure>
        <p>Here&apos;s the parallel to the &ldquo;before Humboldt&rdquo; slide. Our current situation is structurally identical. Popular understanding of technology: UX metaphor animism — deeply anthropocentric. Elite understanding: Silicon Valley platform high-modernism. Scholarly understanding: reactionary anti-technology theologies. The Linnaeus-like taxonomy of the technosphere: &ldquo;product&rdquo;-based, reductionist, blind to emergence and gestalt at the technosphere and geopolitical level. No conception of the planetary. And neo-natural wilderness — all the tech infrastructure — understood as something to be <em>governed</em>, in an almost-colonial mode.</p>
        <p>We are in a very similar situation to the one Humboldt encountered. The Protocol Institute is trying to play the role Humboldt played — for New Nature.</p>
        <figure>
          <img src={`${R2}/slides/slide-16.png`} alt="The 80:20 Version" loading="lazy" />
        </figure>
        <p>Back to the formula. I have an engineering background, so I naturally think in math metaphors. 80% of New Nature can be explained as the convolution of AI and protocols across the planet. Why are AI and protocols such natural duals of each other?</p>
        <p>We&apos;ve been calling this the <a href="https://protocolized.io/p/constructing-the-evil-twin-of-ai">Evil Twins Thesis</a>. Here&apos;s the side-by-side comparison we&apos;ve spent the last year developing:</p>
        <table class="evil-twins">
          <thead><tr><th>AI</th><th>Protocols</th></tr></thead>
          <tbody>
            <tr><td>Intelligent by emergence</td><td>Dumb by design</td></tr>
            <tr><td>Probabilistic</td><td>Deterministic</td></tr>
            <tr><td>World <em>Computer</em></td><td>World <em>Fabric</em></td></tr>
            <tr><td>Oracle side of predictions</td><td>Contracts side of predictions</td></tr>
            <tr><td>Entanglement disposition</td><td>Composability disposition</td></tr>
            <tr><td>Oozy</td><td>Hard</td></tr>
            <tr><td>Muddy Law</td><td>Crystalline Law</td></tr>
            <tr><td>Archival-Carnival temporality</td><td>Clock-driven temporality</td></tr>
            <tr><td>Entropic one-way doors</td><td>Cryptographic one-way doors</td></tr>
            <tr><td>Divergent</td><td>Consensus</td></tr>
            <tr><td>Idiosyncratic</td><td>Standardized</td></tr>
            <tr><td>Turns humans gooey</td><td>Turns humans prickly</td></tr>
            <tr><td>Bouba</td><td>Kiki</td></tr>
            <tr><td><strong>Irresistible Force</strong></td><td><strong>Immovable Objects</strong></td></tr>
          </tbody>
        </table>
        <p>The &ldquo;world computer&rdquo; framing is worth pausing on. When this program came out of the Ethereum ecosystem, the initial vision for Ethereum was <em>the world computer</em>. But now that AI is here, AI is in fact the world computer — and the role of protocols, including blockchains, is as the <em><a href="https://protocolized.io/p/the-fabric-and-the-brain">world fabric</a></em>, weaving all the computational elements together at planetary scale.</p>
        <p>The most important pairing is the last one: AI as irresistible force, protocols as immovable objects. One of the key elements of how protocols work is encryption — especially public key cryptography. That&apos;s the one thing AI can&apos;t brute-force its way through, as long as some form of encryption holds. (If quantum computing breaks all encryption, we&apos;re in much deeper trouble.) This irresistible force / immovable object relationship is central to how you create New Nature out of the combination.</p>
        <p>But the third element is essential.</p>
        <figure>
          <img src={`${R2}/slides/slide-18.png`} alt="Venn diagram: Planetary / AI / Protocols → New Nature" loading="lazy" />
          <figcaption>The three-circle Venn. All three elements are necessary.</figcaption>
        </figure>
        <p>Here&apos;s the Venn diagram of Planetary, AI, and Protocols. Take any two without the third, and you get something recognizable — and bad:</p>
        <p><strong>Protocols alone:</strong> Degen Planet. Everything everybody criticizes about blockchains. Takes the worst of Wall Street and decentralizes it to the individual — meme coins, the casino dynamic.</p>
        <p><strong>AI alone:</strong> Slop Planet. Nothing regulating AI, nothing checking it. Floods of crap across the planet.</p>
        <p><strong>Planetary alone</strong> — technology without the last thirty years of AI and protocols, including the internet and Web 2.0: Enshittified Industrialism. In my opinion, this is the cause of everything going wrong everywhere. Why climate action keeps failing. Why we have so many stupid wars. Enshittified industrialism all the way down. New Nature is our ticket and gateway out of that.</p>
        <p>Now the pairwise intersections:</p>
        <p><strong>AI + Protocols, no Planetary:</strong> Cypherpunk. They start to check and balance each other, and genuinely interesting things happen. But cypherpunk gives you vibes of marginal, peripheral things happening at the edges of the mainstream world. Small scale. The question is how to get to planetary scale — and that&apos;s where the third circle comes in.</p>
        <p><strong>Protocols + Planetary, no AI:</strong> Terminal Financialization. This is where a lot of the crypto world is heading — stablecoins, Wall Street on blockchain rails. A lot of that is genuinely valuable; it&apos;ll reform Wall Street and bring it into this century. But if that&apos;s <em>all</em> that happens: runaway financialization. And I hate the very thought of that.</p>
        <p><strong>AI + Planetary, no Protocols:</strong> Big Brother. Huge frontier foundation models, nation-state-level corporatist connections, surveillance state. Already far along in China, getting there in the US and elsewhere. This is what you get if AI becomes synonymous with a few huge companies that then get into bed with powerful governments and nobody else has control.</p>
        <p><strong>All three together:</strong> New Nature. A genuine three-way balance of power. The world is in a shitty place because of everything going on — but if you get all three working together, positive futures start to become possible.</p>

        <hr />
        <h2 id="pi-positioning">PI Positioning</h2>
        <p>There&apos;s a year of serious thinking behind this picture — not just me making up diagrams in my own head. Here are some outtakes from the three-day strategy retreat Timber, Tim, and I had in April:</p>
        <figure>
          <img src={`${R2}/retreat.png`} alt="Strategy retreat — flip charts on the wall" loading="lazy" />
          <figcaption>PI kickoff strategy retreat (Timber, Tim, Venkat). The flip charts are on my wall now.</figcaption>
        </figure>
        <figure>
          <img src={`${R2}/brainstorm_clean.png`} alt="New Nature concept brainstorm — whiteboard mind map" loading="lazy" />
          <figcaption>The big mind map on the whiteboard behind me — made while preparing this talk.</figcaption>
        </figure>

        <h3 id="pi-in-the-world">PI in the World</h3>
        <div class="fig-row">
          <figure>
            <img src={`${R2}/direct_oblique_2x2_clean.png`} alt="Context Tanks 2×2 — whiteboard" loading="lazy" />
            <figcaption>Whiteboard version.</figcaption>
          </figure>
          <figure>
            <img src={`${R2}/slides/slide-20.png`} alt="PI in the World — 2×2" loading="lazy" />
            <figcaption>Slide version.</figcaption>
          </figure>
        </div>
        <p>The main 2×2 for thinking about how PI fits in the world: x-axis is concern with technology evolution (direct vs. oblique); y-axis is concern with human flourishing (direct vs. oblique).</p>
        <p>Direct on both: the <strong>private sector</strong>. Product, clear benefit to humans, sell it.</p>
        <p>Direct on human flourishing, oblique on technology: <strong>philanthropy and think tanks</strong>. Most of the public sector too.</p>
        <p>Oblique on both: <strong>basic research</strong>. Fundamental research in cryptography, energy, climate — shapes technology without directly becoming it. This infrastructure is breaking, and lots of people are working to fix it, but we&apos;re not in that quadrant.</p>
        <p>We put ourselves in the <strong>top-left quadrant</strong>, which we think essentially doesn&apos;t exist yet: the liminal zone translating the output of basic research into the inputs of the direct-impact sector. We&apos;re calling it <strong>Context Tanks</strong>.</p>

        <h3 id="pi-pipeline-model">PI Pipeline Model</h3>
        <div class="fig-row">
          <figure>
            <img src={`${R2}/pipeline_clean.png`} alt="PI Pipeline Model — whiteboard" loading="lazy" />
            <figcaption>Whiteboard version.</figcaption>
          </figure>
          <figure>
            <img src={`${R2}/slides/slide-21.png`} alt="PI Pipeline Model — slide" loading="lazy" />
            <figcaption>Slide version.</figcaption>
          </figure>
        </div>
        <p>The context tank as pipeline: from undefined knowledge potential (basic research) to defined form factors — tech outputs, arts and culture, markets and the economy, politics and governance. Our job is to create an environment where you can take undefined things and give them the right shape and size to impact the world.</p>

        <h3 id="pi-in-crypto">PI in Crypto</h3>
        <figure class="medium">
          <img src={`${R2}/slides/slide-22.png`} alt="PI in Crypto 2×2 — Priced/Priceless × Small Scale/Planetary" loading="lazy" />
          <figcaption>We want to be in the priceless-planetary quadrant — not the zombie-apocalypse version of cypherpunk.</figcaption>
        </figure>
        <p>Since we came out of the Ethereum ecosystem, we need to know where we stand in crypto. The x-axis: priced vs. priceless goals. The priced side — DeFi, meme coins, stablecoins, Wall Street on blockchain rails — is well understood. The priceless side is about things we consider priceless: freedom, liberty, censorship resistance — things on which you can&apos;t put a price tag. Crypto builds infrastructure to ensure those still exist.</p>
        <p>The small-scale version of priceless: cypherpunk. Important work — running your own nodes, keeping the lights on when nation states fail, maintaining end-to-end encryption infrastructure for others. But I don&apos;t like the idea of crypto as only an apocalyptic technology that kicks in when everything else breaks.</p>
        <p>We want to be in the priceless-planetary quadrant — doing crypto when things <em>haven&apos;t</em> fallen to pieces. In the New Nature world, not the zombie-apocalypse world. Not many people are playing in that quadrant. And a lot of people think we shouldn&apos;t. We disagree.</p>

        <h3 id="pi-in-ai">PI in AI</h3>
        <figure>
          <img src={`${R2}/slides/slide-24.png`} alt="PI in AI (draft) — Control/Plurality × Preservationist/Transformationist" loading="lazy" />
          <figcaption>The entire current discourse lives in the bottom-left quadrant.</figcaption>
        </figure>
        <p>The entire existing discourse about AI lives in what I&apos;m calling the preservationist-control quadrant. &ldquo;Preservationist&rdquo; means treating the current human condition as a sacred thing not to be transformed. &ldquo;Control&rdquo; means wanting to dictate what AI is and does.</p>
        <p>Within that, there&apos;s a sub-2×2: the tech-lash pessimists (stochastic parrots, data center power consumption — willfully blind to what&apos;s actually happening), the LinkedIn optimists (just another enterprise software to adopt), the AGI doom theologians, and e/acc (the valence-flipped theology). I personally hate this entire bottom-left quadrant, and I&apos;m working to make everyone at PI hate it too.</p>
        <p>The canvas is larger. Replace &ldquo;control&rdquo; with &ldquo;plurality&rdquo; on the x-axis — highly diverse, distributed AI, which a lot of us are starting to believe is self-regulating the same way nature self-regulates: through pluralism, Darwinian competition, arms races, open source. On that axis you get d/acc (Vitalik&apos;s cypherpunk framing for AI — still somewhat preservationist) and, at planetary scale, something that doesn&apos;t have a name yet.</p>
        <p>Replace &ldquo;preservationist&rdquo; with &ldquo;transformationist&rdquo; on the y-axis — a vision for what humans can become, not just what we currently are. If you&apos;re still in control mode but transformationist: the billionaire fixations. Longevity, private space programs, gigawatt data centers. Everything Musk and Thiel do. Still an attitude of control towards a transformed human condition, rather than dancing with the new dynamics towards a new way of being.</p>
        <p>The top-right quadrant — transformationist <em>and</em> pluralist — is where essentially nobody is operating. I think 90% of the people in that quadrant are clustered around the Protocol Institute. Maybe that&apos;s hubristic. But I genuinely haven&apos;t had conversations in that quadrant anywhere else.</p>

        <h3 id="research-model-special-interest-groups">Research Model: Special Interest Groups</h3>
        <figure>
          <img src={`${R2}/slides/slide-25.png`} alt="Research Model — Special Interest Groups" loading="lazy" />
        </figure>
        <p>Our research model for operationalizing all this: the Special Interest Groups. We think of SIGs as <strong>attention tunnels</strong> — the smaller-scale version of the Context Tank. This is where projects that don&apos;t have a shape discover their right shape and size — whether it&apos;s going to be a startup, an academic project, protocol standardization, open source, a novel, a movie. If your idea doesn&apos;t know what it wants to be when it grows up, come work with us.</p>

        <h3 id="putting-it-all-together">Putting It All Together</h3>
        <div class="fig-row">
          <figure>
            <img src={`${R2}/newnature_clean.png`} alt="New Nature concentric circles — PI Kernel IP" loading="lazy" />
            <figcaption>Close-up of the concentric circles: PI at center, shells of AI-native and crypto-native practice, education/consulting/monuments, and New Nature as the outer territory to invent and discover.</figcaption>
          </figure>
          <figure>
            <img src={`${R2}/whiteboard_clean.png`} alt="Full whiteboard — 2×2 and concentric circles" loading="lazy" />
            <figcaption>The full whiteboard: Context Tanks 2×2 on the left, the New Nature concentric circles on the right.</figcaption>
          </figure>
        </div>
        <figure>
          <img src={`${R2}/slides/slide-26.png`} alt="Putting it all together — org diagram" loading="lazy" />
        </figure>

        <hr />
        <h2 id="money-matters">Money Matters</h2>
        <figure>
          <img src={`${R2}/slides/slide-27.png`} alt="Money Matters — What will this cost?" loading="lazy" />
        </figure>
        <p>The Protocol Institute has operated on roughly $3M over three years in the Summer of Protocols phase. As we incorporate as an independent Canadian nonprofit, our target for the next twelve months is $500K–$1.5M — covering everything from keeping the lights on to a full healthy operating budget. Funding comes from a mix of publishing and consulting revenue, funded research partnerships, and institutional and individual grants. If you&apos;d like to support the work, see our <a href="https://protocol-institute.org/support.html">support page</a>.</p>
        <figure class="medium">
          <img src={`${R2}/slides/slide-28.png`} alt="In closing — 3 calls to action" loading="lazy" />
        </figure>

        {/* Related resources */}
        <div class="essay-related">
          <h2>Related Resources</h2>
          <div class="related-cards">
            <a href="https://files.protocolized.io/features/new-nature-slides.pdf" class="related-card" target="_blank" rel="noopener noreferrer">
              <div class="related-card-type">Handout &rarr; PDF</div>
              <div class="related-card-title">New Nature — Talk Slides (June 2026)</div>
            </a>
            <a href="https://www.youtube.com/watch?v=U4lSY7BX228" class="related-card" target="_blank" rel="noopener noreferrer">
              <div class="related-card-type">Talk &rarr; YouTube</div>
              <div class="related-card-title">New Nature — Full Talk Recording</div>
            </a>
            <a href="/resources/inventing-new-nature" class="related-card">
              <div class="related-card-type">Article</div>
              <div class="related-card-title">Inventing New Nature</div>
            </a>
          </div>
        </div>

      </div>
    </Base>
  );
}
