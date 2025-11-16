import React, { useState } from 'react';
import { View, TextInput, Button, Text, ScrollView, StyleSheet } from 'react-native';
import axios from 'axios';

export default function ChatbotScreen() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [intent, setIntent] = useState(null);
  const [lastActionableIntent, setLastActionableIntent] = useState(null);
  const [letter, setLetter] = useState(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { from: 'user', text: input }];
    setMessages(newMessages);
    setInput('');

    try {
      const res = await axios.post('http://localhost:5000/chat', {
        query: input,
        lang: 'en',
      });

      const reply = res.data.reply;
      const intentFromBot = res.data.intent;

      // Save chatbot reply
      setMessages([...newMessages, { from: 'bot', text: reply }]);
      setIntent(intentFromBot);

      // Save last actionable intent
      if (intentFromBot === 'landlord_complaint' || intentFromBot === 'rti_request') {
        setLastActionableIntent(intentFromBot);
      }

      // Special case: user says "yes" and chatbot doesn't give a new intent
      if (input.toLowerCase() === 'yes' && !intentFromBot && lastActionableIntent) {
        setIntent(lastActionableIntent); // Restore previous actionable intent
      }

    } catch (error) {
      setMessages([...newMessages, { from: 'bot', text: 'Error connecting to backend.' }]);
    }
  };

  const generateLetter = async () => {
    try {
      const res = await axios.post('http://localhost:5000/generate_letter', {
        type: intent,
        details: {
          tenant_name: 'Ravi Kumar',
          landlord_name: 'Mr. Sharma',
          name: 'Ravi Kumar',       // Used in RTI letter fallback
          query: 'Information regarding property rights' // fallback
        }
      });
      setLetter(res.data.letter);
    } catch (error) {
      setLetter('Error generating letter. Please try again.');
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.chatBox}>
        {messages.map((msg, index) => (
          <Text key={index} style={msg.from === 'user' ? styles.userText : styles.botText}>
            {msg.from === 'user' ? 'You: ' : 'Saathi: '}
            {msg.text}
          </Text>
        ))}
        {letter && (
          <View style={{ marginTop: 10 }}>
            <Text style={styles.botText}>📄 Generated Letter:</Text>
            <Text style={styles.letterText}>{letter}</Text>
          </View>
        )}
      </ScrollView>

      {intent && (intent === 'landlord_complaint' || intent === 'rti_request') && (
        <Button title="Generate Letter" onPress={generateLetter} />
      )}

      <TextInput
        placeholder="Ask your legal question"
        value={input}
        onChangeText={setInput}
        style={styles.input}
      />
      <Button title="Send" onPress={sendMessage} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  chatBox: { flex: 1, marginBottom: 10 },
  input: { borderWidth: 1, padding: 10, marginVertical: 10, borderRadius: 5 },
  userText: { alignSelf: 'flex-end', marginVertical: 2, color: 'blue' },
  botText: { alignSelf: 'flex-start', marginVertical: 2, color: 'green' },
  letterText: { color: 'black', marginTop: 5, backgroundColor: '#f1f1f1', padding: 8, borderRadius: 5 }
});
