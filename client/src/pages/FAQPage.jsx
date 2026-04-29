import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const faqs = [
  {
    id: "faq-1",
    question: "How do I register to vote?",
    answer: "You can register to vote by filling out Form 6 online via the official Voters' Services Portal (voters.eci.gov.in) or the Voter Helpline App. You can also submit a physical copy of Form 6 to your Electoral Registration Officer (ERO)."
  },
  {
    id: "faq-2",
    question: "How can I check if my name is on the Voter List?",
    answer: "You can search for your name on the electoral roll by visiting the Voters' Services Portal and using the 'Search in Electoral Roll' feature with your EPIC number, personal details, or mobile number."
  },
  {
    id: "faq-3",
    question: "What documents do I need on polling day?",
    answer: "You must carry your Voter ID card (EPIC). If you do not have an EPIC, you can carry other ECI-approved photo identity documents such as Aadhaar Card, PAN Card, Driving License, Indian Passport, or a Passbook with a photograph issued by a Bank/Post Office."
  },
  {
    id: "faq-4",
    question: "What is an EVM and VVPAT?",
    answer: "EVM stands for Electronic Voting Machine, which is used to record votes. VVPAT stands for Voter Verifiable Paper Audit Trail. It is a machine attached to the EVM that prints a paper slip containing the serial number, name, and symbol of the chosen candidate, allowing the voter to verify their vote."
  },
  {
    id: "faq-5",
    question: "How are votes counted?",
    answer: "Votes are counted under the strict supervision of the Returning Officer and in the presence of candidates or their appointed agents. The process is fully transparent and the results are updated in real-time on the ECI Results portal."
  },
  {
    id: "faq-6",
    question: "What is NOTA?",
    answer: "NOTA stands for 'None Of The Above'. It is an option on the EVM that allows a voter to officially reject all the candidates contesting in that particular constituency. It empowers voters to express their dissatisfaction."
  },
  {
    id: "faq-7",
    question: "How does VoteWise ensure the Party Directory is neutral?",
    answer: "Our Party Directory strictly lists the recognized National Parties as classified by the ECI. We only present basic, factual data (founding year, symbol, leadership) without any praise, criticism, or commentary on their achievements or controversies."
  }
];

const AccordionItem = ({ faq, isOpen, onClick }) => {
  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={onClick}
        aria-expanded={isOpen}
        aria-controls={`faq-answer-${faq.id}`}
        id={`faq-question-${faq.id}`}
        className="w-full text-left py-5 px-6 flex justify-between items-center focus:outline-none focus:ring-2 focus:ring-primary focus:bg-background/50 hover:bg-background/50 transition-colors"
      >
        <span className="font-semibold text-text text-lg pr-8">{faq.question}</span>
        {isOpen ? (
          <ChevronUp className="text-secondary flex-shrink-0" size={24} />
        ) : (
          <ChevronDown className="text-muted flex-shrink-0" size={24} />
        )}
      </button>
      <div 
        id={`faq-answer-${faq.id}`}
        role="region"
        aria-labelledby={`faq-question-${faq.id}`}
        className={`px-6 overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 py-4 opacity-100' : 'max-h-0 py-0 opacity-0'}`}
      >
        <p className="text-muted leading-relaxed">{faq.answer}</p>
      </div>
    </div>
  );
};

const FAQPage = () => {
  const [openId, setOpenId] = useState(null);

  const toggleAccordion = (id) => {
    setOpenId(openId === id ? null : id);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="Frequently Asked Questions" 
        subtitle="Common beginner queries about the Indian electoral process."
      />
      
      <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden mt-8">
        {faqs.map((faq) => (
          <AccordionItem 
            key={faq.id} 
            faq={faq} 
            isOpen={openId === faq.id} 
            onClick={() => toggleAccordion(faq.id)} 
          />
        ))}
      </div>
    </div>
  );
};

export default FAQPage;
