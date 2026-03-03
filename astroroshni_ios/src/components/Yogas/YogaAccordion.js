import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../../context/ThemeContext';
import Ionicons from '@expo/vector-icons/Ionicons';

const YogaAccordion = ({ title, data }) => {
    const { theme } = useTheme();
    const [expanded, setExpanded] = useState(false);

    const toggleExpand = () => {
        setExpanded(!expanded);
    };

    return (
        <View style={[styles.container, { backgroundColor: theme.cardColor, borderColor: theme.borderColor }]}>
            <TouchableOpacity onPress={toggleExpand} style={styles.header}>
                <Text style={[styles.title, { color: theme.textColor }]}>{title}</Text>
                <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={24} color={theme.textColor} />
            </TouchableOpacity>
            {expanded && (
                <View style={styles.content}>
                    {data && data.length > 0 ? (
                        data.map((yoga, index) => (
                            <View key={index} style={[styles.yogaItem, { borderBottomColor: theme.borderColor }]}>
                                <Text style={[styles.yogaName, { color: theme.primaryColor }]}>{yoga.name}</Text>
                                <Text style={[styles.yogaDescription, { color: theme.textColor }]}>{yoga.description}</Text>
                            </View>
                        ))
                    ) : (
                        <Text style={{ color: theme.textColor }}>No yogas in this category.</Text>
                    )}
                </View>
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginHorizontal: 10,
        marginVertical: 5,
        borderRadius: 10,
        borderWidth: 1,
        overflow: 'hidden',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 15,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
    },
    content: {
        padding: 15,
    },
    yogaItem: {
        marginBottom: 10,
        paddingBottom: 10,
        borderBottomWidth: 1,
    },
    yogaName: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    yogaDescription: {
        fontSize: 14,
    },
});

export default YogaAccordion;
